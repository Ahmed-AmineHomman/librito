"""Assemble a fixed-layout EPUB book from storybook pages and illustrations."""

from __future__ import annotations

import sys
import shutil
import zipfile
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent
from typing import Sequence
from uuid import NAMESPACE_URL, uuid5
from xml.sax.saxutils import escape

import logging

from PIL import Image, ImageColor, ImageDraw, ImageFont, ImageOps

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from librito.environment import load_repository_environment
from librito.io import load_storybook
from librito.logging import add_logging_arguments, configure_logging
from librito.models import BookParts, PageSpec, Storybook
from librito.workspace import StoryWorkspace

logger = logging.getLogger(__name__)

PAGE_WIDTH = 1600
PAGE_HEIGHT = 2560
BASE_PAGE_AREA = PAGE_WIDTH * PAGE_HEIGHT
TEXT_MARGIN_X = 170
TEXT_MARGIN_Y = 220
BODY_FONT_SIZE = 58
BODY_LINE_SPACING = 22
TITLE_FONT_SIZE = 126
TITLE_LINE_SPACING = 28
AUTHOR_FONT_SIZE = 68
AUTHOR_LINE_SPACING = 18
DEFAULT_BACKGROUND_COLOR = "#f6f1e8"
DEFAULT_TEXT_COLOR = "#1d1a17"
SCALE_FACTOR = 1.0


def scale(
    value: float,
) -> int:
    """Scale a pixel measurement by the current scale factor.

    Parameters
    ----------
    value:
        Pixel value to scale.

    Returns
    -------
    int
        Scaled pixel value.
    """
    return int(value * SCALE_FACTOR)


@dataclass(slots=True)
class RenderedPage:
    """One rendered page staged into the EPUB package.

    Parameters
    ----------
    slug:
        Stable slug used for filenames and manifest identifiers.
    title:
        Human-readable page title for EPUB metadata.
    alt_text:
        Alternative text describing the page image.
    image:
        Fully rendered page image.
    spread:
        Optional EPUB spread side, either ``"left"`` or ``"right"``.
    nav_label:
        Optional navigation label shown in the table of contents.
    """

    slug: str
    title: str
    alt_text: str
    image: Image.Image
    spread: str | None = None
    nav_label: str | None = None


def load_parameters(argv: Sequence[str] | None = None) -> Namespace:
    """Parse command-line arguments.

    Parameters
    ----------
    argv:
        Optional command-line argument sequence.

    Returns
    -------
    Namespace
        Parsed command-line arguments.
    """

    parser = ArgumentParser(
        description=dedent(
            """
            Assemble a fixed-layout EPUB book from a storybook.

            The command validates the required book parts, scene material, and
            referenced illustration files, then renders front matter, scene
            spreads, optional closing pages, and the back cover.
            """
        ).strip(),
        epilog=dedent(
            """
            Behavior:
              - reads ``database/<story>/story.json``
              - validates the title, author, book-part assets, scene texts, and generated illustrations
              - matches the page geometry to the requested aspect ratio
              - renders front matter, one text page and one image page per scene, optional closing pages, and the back cover
              - writes the final EPUB to ``database/<story>/story.epub``

            Layout:
              - front cover: full-page illustration with optional overlaid title and author
              - front matter: paired spreads with blank filler pages when needed
              - each scene: exactly 2 pages
              - closing matter: optional paired spread before the back cover
              - back cover: teaser page with optional full-page illustration

            Examples:
              python helpers/assemble_book.py --story sir_turnip
              python helpers/assemble_book.py --story sir_turnip --aspect-ratio 3:4
              python helpers/assemble_book.py --story sir_turnip --background-color "#f4efe6"
            """
        ).strip(),
        formatter_class=RawDescriptionHelpFormatter,
    )
    add_logging_arguments(parser)
    parser.add_argument(
        "--story",
        required=True,
        type=str,
        help="Story folder name under ./database/<story>/.",
    )
    parser.add_argument(
        "--aspect-ratio",
        default="1:1",
        help="Requested image aspect ratio.",
    )
    parser.add_argument(
        "--background-color",
        default=DEFAULT_BACKGROUND_COLOR,
        help=f"Solid background color for text pages and blank pages (default: {DEFAULT_BACKGROUND_COLOR}).",
    )
    parser.add_argument(
        "--text-color",
        default=DEFAULT_TEXT_COLOR,
        help=f"Text color for rendered text overlays and text pages (default: {DEFAULT_TEXT_COLOR}).",
    )
    parser.add_argument(
        "--resolution",
        choices=["512", "1k", "2k", "1K", "2K"],
        help="Resolution preset for the generated EPUB images (choices: '512', '1k', '2k').",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the book assembly entrypoint.

    Parameters
    ----------
    argv:
        Optional command-line argument sequence.

    Returns
    -------
    int
        Process exit status.
    """

    load_repository_environment()
    arguments = load_parameters(argv)
    configure_logging(arguments.log_level)
    workspace = StoryWorkspace.from_story(arguments.story)
    configure_page_size(arguments.aspect_ratio, arguments.resolution)
    background_color = ImageColor.getrgb(arguments.background_color)
    text_color = ImageColor.getrgb(arguments.text_color)

    logger.info("Starting assembly pipeline for story '%s'.", workspace.story)
    logger.info(
        "Using page size %dx%d for aspect ratio %s.",
        PAGE_WIDTH,
        PAGE_HEIGHT,
        arguments.aspect_ratio,
    )
    story_path = workspace.require_storybook_file()
    logger.info("Loading storybook from %s.", story_path)
    storybook = load_storybook(story_path)
    validate_storybook(storybook, workspace)

    output_path = workspace.book_file
    output_path.parent.mkdir(parents=True, exist_ok=True)

    staging_root = workspace.directory / "_book_assembly_tmp"
    if staging_root.exists():
        if staging_root.parent != workspace.directory:
            raise SystemExit(f"Refusing to clear unexpected staging directory: {staging_root}")
        shutil.rmtree(staging_root)

    try:
        epub_root = staging_root / "EPUB"
        images_directory = epub_root / "images"
        pages_directory = epub_root / "pages"
        meta_inf_directory = staging_root / "META-INF"
        images_directory.mkdir(parents=True, exist_ok=True)
        pages_directory.mkdir(parents=True, exist_ok=True)
        meta_inf_directory.mkdir(parents=True, exist_ok=True)

        logger.info("Rendering cover, front matter, scene spreads, and back matter.")
        pages = build_rendered_pages(
            storybook=storybook,
            workspace=workspace,
            background_color=background_color,
            text_color=text_color,
        )

        manifest_items = [
            '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
            '<item id="stylesheet" href="styles.css" media-type="text/css"/>',
        ]
        spine_items: list[str] = []
        nav_links: list[str] = []

        for page in pages:
            image_name = f"{page.slug}.png"
            page_name = f"{page.slug}.xhtml"
            image_item_id = f"{page.slug}-image"
            page_item_id = f"{page.slug}-page"

            page.image.save(images_directory / image_name)
            (pages_directory / page_name).write_text(
                build_page_document(
                    title=page.title,
                    image_href=f"../images/{image_name}",
                    image_alt=page.alt_text,
                ),
                encoding="utf-8",
            )

            image_item = (
                f'<item id="{image_item_id}" href="images/{image_name}" media-type="image/png"/>'
            )
            if page.slug == "front-cover":
                image_item = (
                    f'<item id="{image_item_id}" href="images/{image_name}" '
                    'media-type="image/png" properties="cover-image"/>'
                )

            manifest_items.extend(
                [
                    image_item,
                    f'<item id="{page_item_id}" href="pages/{page_name}" media-type="application/xhtml+xml"/>',
                ]
            )

            if page.spread == "left":
                spine_items.append(f'<itemref idref="{page_item_id}" properties="page-spread-left"/>')
            elif page.spread == "right":
                spine_items.append(f'<itemref idref="{page_item_id}" properties="page-spread-right"/>')
            else:
                spine_items.append(f'<itemref idref="{page_item_id}"/>')

            if page.nav_label:
                nav_links.append(f'<li><a href="pages/{page_name}">{escape(page.nav_label)}</a></li>')

        (epub_root / "styles.css").write_text(build_stylesheet(), encoding="utf-8")
        (epub_root / "nav.xhtml").write_text(
            build_navigation_document(storybook.title, nav_links),
            encoding="utf-8",
        )
        (epub_root / "package.opf").write_text(
            build_package_document(workspace, storybook, manifest_items, spine_items),
            encoding="utf-8",
        )
        (meta_inf_directory / "container.xml").write_text(build_container_document(), encoding="utf-8")
        (staging_root / "mimetype").write_text("application/epub+zip", encoding="utf-8")

        temporary_output_path = output_path.with_suffix(".tmp")
        write_epub_archive(staging_root, temporary_output_path)
        temporary_output_path.replace(output_path)
    finally:
        if staging_root.exists():
            if staging_root.parent != workspace.directory:
                raise SystemExit(f"Refusing to clear unexpected staging directory: {staging_root}")
            shutil.rmtree(staging_root)

    logger.info("Wrote book to %s.", output_path)
    logger.info("Done.")
    return 0


def configure_page_size(
    aspect_ratio: str,
    resolution: str | None = None,
) -> None:
    """Configure the single-page size from a ``width:height`` ratio string.

    Parameters
    ----------
    aspect_ratio:
        Aspect ratio string such as ``"1:1"`` or ``"3:4"``.
    resolution:
        Optional resolution preset string.

    Raises
    ------
    SystemExit
        If the aspect ratio is malformed or non-positive.
    """

    width_text, separator, height_text = aspect_ratio.partition(":")
    if separator != ":":
        raise SystemExit(
            f"Invalid aspect ratio {aspect_ratio!r}. Expected a value like '1:1' or '3:4'."
        )

    try:
        width_ratio = float(width_text)
        height_ratio = float(height_text)
    except ValueError as error:
        raise SystemExit(
            f"Invalid aspect ratio {aspect_ratio!r}. Expected numeric values like '1:1' or '3:4'."
        ) from error

    if width_ratio <= 0 or height_ratio <= 0:
        raise SystemExit(f"Aspect ratio values must be positive, got {aspect_ratio!r}.")

    ratio = width_ratio / height_ratio
    global PAGE_WIDTH, PAGE_HEIGHT, SCALE_FACTOR
    default_width = round((BASE_PAGE_AREA * ratio) ** 0.5)

    if resolution is not None:
        res_lower = resolution.lower()
        if res_lower == "512":
            target_area = 512 * 512
        elif res_lower == "1k":
            target_area = 1024 * 1024
        elif res_lower == "2k":
            target_area = 2048 * 2048
        else:
            raise SystemExit(f"Invalid resolution value: {resolution!r}")

        PAGE_WIDTH = round((target_area * ratio) ** 0.5)
        PAGE_HEIGHT = round((target_area / ratio) ** 0.5)
        SCALE_FACTOR = PAGE_WIDTH / default_width
    else:
        PAGE_WIDTH = default_width
        PAGE_HEIGHT = round((BASE_PAGE_AREA / ratio) ** 0.5)
        SCALE_FACTOR = 1.0


def build_rendered_pages(
    storybook: Storybook,
    workspace: StoryWorkspace,
    background_color: tuple[int, int, int],
    text_color: tuple[int, int, int],
) -> list[RenderedPage]:
    """Render every book page in display order."""

    pages: list[RenderedPage] = [
        RenderedPage(
            slug="front-cover",
            title="Front Cover",
            alt_text=f"Front cover for {storybook.title}",
            image=render_front_cover_page(
                title=storybook.title,
                author=storybook.author,
                image_path=workspace.directory / storybook.parts.front_cover.illustration.image_path,
                text_mode=storybook.parts.front_cover.illustration.text_mode,
                text_color=text_color,
            ),
            nav_label="Front Cover",
        )
    ]

    pages.extend(
        build_opening_pair(
            parts=storybook.parts,
            workspace=workspace,
            background_color=background_color,
            text_color=text_color,
        )
    )
    pages.extend(
        build_title_pair(
            storybook=storybook,
            workspace=workspace,
            background_color=background_color,
            text_color=text_color,
        )
    )

    for scene_number, scene in enumerate(storybook.scenes, start=1):
        logger.info(
            "Rendering spread for scene %d/%d (%s).",
            scene_number,
            len(storybook.scenes),
            scene.label,
        )
        pages.extend(
            [
                RenderedPage(
                    slug=f"scene-{scene_number:03d}-text",
                    title=f"Scene {scene_number}",
                    alt_text=f"Scene {scene_number} text",
                    image=render_scene_text_page(
                        scene.label,
                        scene.text,
                        background_color,
                        text_color,
                    ),
                    spread="left",
                    nav_label=f"Scene {scene_number}",
                ),
                RenderedPage(
                    slug=f"scene-{scene_number:03d}-illustration",
                    title=f"Scene {scene_number} Illustration",
                    alt_text=f"Scene {scene_number} illustration",
                    image=render_illustration_page(workspace.directory / scene.image_path),
                    spread="right",
                ),
            ]
        )

    pages.extend(
        build_closing_pair(
            parts=storybook.parts,
            workspace=workspace,
            background_color=background_color,
            text_color=text_color,
        )
    )
    pages.append(
        RenderedPage(
            slug="back-cover",
            title="Back Cover",
            alt_text=f"Back cover for {storybook.title}",
            image=render_back_cover_page(
                back_cover=storybook.parts.back_cover,
                workspace=workspace,
                background_color=background_color,
                text_color=text_color,
            ),
            nav_label="Back Cover",
        )
    )
    return pages


def build_opening_pair(
    parts: BookParts,
    workspace: StoryWorkspace,
    background_color: tuple[int, int, int],
    text_color: tuple[int, int, int],
) -> list[RenderedPage]:
    """Render the front-endpaper and opening-page spread when needed."""

    has_left = parts.front_endpaper is not None and parts.front_endpaper.illustration is not None
    has_right = has_page_text_content(parts.opening_page)
    if not has_left and not has_right:
        return []

    return [
        RenderedPage(
            slug="front-endpaper" if has_left else "front-endpaper-blank",
            title="Front Endpaper" if has_left else "Blank",
            alt_text="Front endpaper" if has_left else "Blank page",
            image=render_illustrated_page(parts.front_endpaper, workspace, background_color),
            spread="left",
            nav_label="Front Endpaper" if has_left else None,
        ),
        RenderedPage(
            slug="opening-page" if has_right else "opening-page-blank",
            title="Opening Page" if has_right else "Blank",
            alt_text="Dedication or epigraph page" if has_right else "Blank page",
            image=render_text_page(parts.opening_page, background_color, text_color, "The opening-page text does not fit on its page."),
            spread="right",
            nav_label="Dedication / Epigraph" if has_right else None,
        ),
    ]


def build_title_pair(
    storybook: Storybook,
    workspace: StoryWorkspace,
    background_color: tuple[int, int, int],
    text_color: tuple[int, int, int],
) -> list[RenderedPage]:
    """Render the frontispiece and title-page spread."""

    has_frontispiece = storybook.parts.frontispiece is not None and storybook.parts.frontispiece.illustration is not None
    return [
        RenderedPage(
            slug="frontispiece" if has_frontispiece else "frontispiece-blank",
            title="Frontispiece" if has_frontispiece else "Blank",
            alt_text="Frontispiece illustration" if has_frontispiece else "Blank page",
            image=render_illustrated_page(storybook.parts.frontispiece, workspace, background_color),
            spread="left",
            nav_label="Frontispiece" if has_frontispiece else None,
        ),
        RenderedPage(
            slug="title-page",
            title="Title Page",
            alt_text=f"Title page for {storybook.title}",
            image=render_title_page(
                title=storybook.title,
                author=storybook.author,
                title_page=storybook.parts.title_page,
                workspace=workspace,
                background_color=background_color,
                text_color=text_color,
            ),
            spread="right",
            nav_label="Title Page",
        ),
    ]


def build_closing_pair(
    parts: BookParts,
    workspace: StoryWorkspace,
    background_color: tuple[int, int, int],
    text_color: tuple[int, int, int],
) -> list[RenderedPage]:
    """Render the optional closing spread."""

    has_left = has_page_text_content(parts.closing_facing_page)
    has_right = parts.closing_illustration is not None and parts.closing_illustration.illustration is not None
    if not has_left and not has_right:
        return []

    return [
        RenderedPage(
            slug="closing-facing-page" if has_left else "closing-facing-page-blank",
            title="Closing Facing Page" if has_left else "Blank",
            alt_text="Closing facing page" if has_left else "Blank page",
            image=render_text_page(
                parts.closing_facing_page,
                background_color,
                text_color,
                "The closing-facing-page text does not fit on its page.",
            ),
            spread="left",
            nav_label="Closing Page" if has_left else None,
        ),
        RenderedPage(
            slug="closing-illustration" if has_right else "closing-illustration-blank",
            title="Closing Illustration" if has_right else "Blank",
            alt_text="Closing illustration" if has_right else "Blank page",
            image=render_illustrated_page(parts.closing_illustration, workspace, background_color),
            spread="right",
            nav_label="Closing Illustration" if has_right else None,
        ),
    ]


def validate_storybook(storybook: Storybook, workspace: StoryWorkspace) -> None:
    """Validate that the storybook contains everything required for assembly.

    Parameters
    ----------
    storybook:
        Parsed storybook to validate.
    workspace:
        Filesystem workspace containing the story assets.

    Raises
    ------
    SystemExit
        If any required assembly material is missing or invalid.
    """

    if not storybook.title.strip():
        raise SystemExit("The storybook title must be a non-empty string before assembly.")
    if not storybook.author.strip():
        raise SystemExit("The storybook author must be a non-empty string before assembly.")
    if not storybook.scenes:
        raise SystemExit("The storybook does not contain any scenes to assemble.")
    if not any(text.strip() for text in storybook.parts.back_cover.text):
        raise SystemExit("The back cover teaser must be a non-empty string before assembly.")
    if storybook.parts.front_cover.illustration is None:
        raise SystemExit("The front cover must define an illustration before assembly.")

    validate_image_path(
        workspace,
        storybook.parts.front_cover.illustration.image_path,
        "Front cover illustration",
    )
    validate_optional_illustrated_page(workspace, storybook.parts.front_endpaper, "Front endpaper illustration")
    validate_optional_illustrated_page(workspace, storybook.parts.frontispiece, "Frontispiece illustration")
    validate_optional_illustrated_page(
        workspace,
        storybook.parts.closing_illustration,
        "Closing illustration",
    )
    if storybook.parts.title_page.illustration is not None:
        validate_image_path(
            workspace,
            storybook.parts.title_page.illustration.image_path,
            "Title page illustration",
        )
    if storybook.parts.back_cover.illustration is not None:
        validate_image_path(
            workspace,
            storybook.parts.back_cover.illustration.image_path,
            "Back cover illustration",
        )

    for scene_number, scene in enumerate(storybook.scenes, start=1):
        if not scene.text.strip():
            raise SystemExit(f"Scene {scene_number} ({scene.label}) has empty text.")
        if not scene.image_path.strip():
            raise SystemExit(f"Scene {scene_number} ({scene.label}) is missing image_path.")
        validate_image_path(
            workspace,
            scene.image_path,
            f"Scene {scene_number} ({scene.label}) illustration",
        )


def validate_optional_illustrated_page(
    workspace: StoryWorkspace,
    page: PageSpec | None,
    label: str,
) -> None:
    """Validate an optional illustrated page if present."""

    if page is None or page.illustration is None:
        return
    validate_image_path(workspace, page.illustration.image_path, label)


def validate_image_path(workspace: StoryWorkspace, relative_path: str, label: str) -> None:
    """Validate that a referenced image exists and is readable."""

    if not relative_path.strip():
        raise SystemExit(f"{label} is missing image_path.")

    image_path = workspace.directory / relative_path
    if not image_path.is_file():
        raise SystemExit(f"{label} is missing its illustration file: {image_path}")

    try:
        with Image.open(image_path) as image:
            image.verify()
    except Exception as error:
        raise SystemExit(f"{label} could not be opened: {image_path}") from error


def render_cover_page(
    title: str,
    background_color: tuple[int, int, int],
    text_color: tuple[int, int, int],
) -> Image.Image:
    """Render the title-only cover page.

    Parameters
    ----------
    title:
        Story title to render.
    background_color:
        RGB page background color.
    text_color:
        RGB text color.

    Returns
    -------
    Image.Image
        Rendered cover page image.

    Raises
    ------
    SystemExit
        If the title does not fit on the cover.
    """

    page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), background_color)
    draw = ImageDraw.Draw(page)
    available_width = PAGE_WIDTH - (scale(TEXT_MARGIN_X) * 2)
    available_height = PAGE_HEIGHT - (scale(TEXT_MARGIN_Y) * 2)

    for font_size in (scale(TITLE_FONT_SIZE), scale(112), scale(100), scale(90), scale(82), scale(74)):
        font = load_font(font_size, bold=True)
        lines = wrap_text(title, draw, font, available_width)
        line_height = font.size + scale(TITLE_LINE_SPACING)
        text_height = len(lines) * line_height - scale(TITLE_LINE_SPACING)
        if text_height > available_height:
            continue

        y = scale(TEXT_MARGIN_Y) + ((available_height - text_height) // 2)
        for line in lines:
            line_bbox = draw.textbbox((0, 0), line, font=font)
            line_width = line_bbox[2] - line_bbox[0]
            x = (PAGE_WIDTH - line_width) // 2
            draw.text((x, y), line, fill=text_color, font=font)
            y += line_height
        return page

    raise SystemExit("The story title does not fit on the cover page.")


def render_front_cover_page(
    title: str,
    author: str,
    image_path: Path,
    text_mode: str | None,
    text_color: tuple[int, int, int],
) -> Image.Image:
    """Render the front cover."""

    page = render_illustration_page(image_path)
    if text_mode == "embedded":
        return page

    canvas = page.convert("RGBA")
    draw = ImageDraw.Draw(canvas, "RGBA")
    panel_top = round(PAGE_HEIGHT * 0.30)
    panel_bottom = round(PAGE_HEIGHT * 0.72)
    draw.rectangle(
        [(scale(TEXT_MARGIN_X) - scale(30), panel_top), (PAGE_WIDTH - scale(TEXT_MARGIN_X) + scale(30), panel_bottom)],
        fill=(255, 255, 255, 170),
    )

    title_box_top = panel_top + scale(70)
    title_box_height = round((panel_bottom - panel_top) * 0.55)
    draw_centered_text_block(
        draw=draw,
        text=title,
        box=(scale(TEXT_MARGIN_X), title_box_top, PAGE_WIDTH - scale(TEXT_MARGIN_X), title_box_top + title_box_height),
        font_sizes=[scale(fs) for fs in (TITLE_FONT_SIZE, 112, 100, 90, 82, 74)],
        line_spacing=scale(TITLE_LINE_SPACING),
        text_color=text_color,
        bold=True,
        error_message="The story title does not fit on the front cover.",
    )
    draw_centered_text_block(
        draw=draw,
        text=author,
        box=(scale(TEXT_MARGIN_X), panel_bottom - scale(230), PAGE_WIDTH - scale(TEXT_MARGIN_X), panel_bottom - scale(90)),
        font_sizes=[scale(fs) for fs in (AUTHOR_FONT_SIZE, 62, 56, 50)],
        line_spacing=scale(AUTHOR_LINE_SPACING),
        text_color=text_color,
        bold=False,
        error_message="The story author does not fit on the front cover.",
    )
    return canvas.convert("RGB")


def render_title_page(
    title: str,
    author: str,
    title_page: PageSpec,
    workspace: StoryWorkspace,
    background_color: tuple[int, int, int],
    text_color: tuple[int, int, int],
) -> Image.Image:
    """Render the title page."""

    page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), background_color)
    draw = ImageDraw.Draw(page)

    title_top = round(PAGE_HEIGHT * 0.14)
    title_bottom = round(PAGE_HEIGHT * (0.54 if title_page.illustration is None else 0.42))
    draw_centered_text_block(
        draw=draw,
        text=title,
        box=(scale(TEXT_MARGIN_X), title_top, PAGE_WIDTH - scale(TEXT_MARGIN_X), title_bottom),
        font_sizes=[scale(fs) for fs in (110, 98, 88, 78, 70)],
        line_spacing=scale(24),
        text_color=text_color,
        bold=True,
        error_message="The story title does not fit on the title page.",
    )
    draw_centered_text_block(
        draw=draw,
        text=author,
        box=(scale(TEXT_MARGIN_X), title_bottom + scale(30), PAGE_WIDTH - scale(TEXT_MARGIN_X), title_bottom + scale(180)),
        font_sizes=[scale(fs) for fs in (AUTHOR_FONT_SIZE, 62, 56, 50)],
        line_spacing=scale(AUTHOR_LINE_SPACING),
        text_color=text_color,
        bold=False,
        error_message="The story author does not fit on the title page.",
    )

    if title_page.illustration is not None:
        illustration = render_illustration_page(workspace.directory / title_page.illustration.image_path)
        illustration.thumbnail((round(PAGE_WIDTH * 0.34), round(PAGE_HEIGHT * 0.20)))
        illustration_x = (PAGE_WIDTH - illustration.width) // 2
        illustration_y = round(PAGE_HEIGHT * 0.70) - (illustration.height // 2)
        page.paste(illustration, (illustration_x, illustration_y))

    return page


def render_text_page(
    page: PageSpec | None,
    background_color: tuple[int, int, int],
    text_color: tuple[int, int, int],
    error_message: str,
) -> Image.Image:
    """Render one generic text page or a blank fallback."""

    if not has_page_text_content(page):
        return render_blank_page(background_color)

    return render_centered_text_page(
        text="\n\n".join(text.strip() for text in page.text if text.strip()),
        background_color=background_color,
        text_color=text_color,
        error_message=error_message,
    )


def render_scene_text_page(
    scene_label: str,
    text: str,
    background_color: tuple[int, int, int],
    text_color: tuple[int, int, int],
) -> Image.Image:
    """Render one left-page text panel for a scene.

    Parameters
    ----------
    scene_label:
        Stable scene label used in overflow errors.
    text:
        Reader-facing scene text.
    background_color:
        RGB page background color.
    text_color:
        RGB text color.

    Returns
    -------
    Image.Image
        Rendered text page image.

    Raises
    ------
    SystemExit
        If the scene text cannot fit on a single page.
    """

    page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), background_color)
    draw = ImageDraw.Draw(page)
    font = load_font(scale(BODY_FONT_SIZE))
    available_width = PAGE_WIDTH - (scale(TEXT_MARGIN_X) * 2)
    available_height = PAGE_HEIGHT - (scale(TEXT_MARGIN_Y) * 2)
    lines = wrap_text(text, draw, font, available_width)
    line_height = scale(BODY_FONT_SIZE) + scale(BODY_LINE_SPACING)
    text_height = len(lines) * line_height - scale(BODY_LINE_SPACING)
    if text_height > available_height:
        raise SystemExit(
            f"Scene {scene_label!r} text does not fit on its single left page."
        )

    y = scale(TEXT_MARGIN_Y) + ((available_height - text_height) // 2)
    for line in lines:
        if line:
            draw.text((scale(TEXT_MARGIN_X), y), line, fill=text_color, font=font)
        y += line_height

    return page


def render_illustration_page(image_path: Path) -> Image.Image:
    """Render one full-page illustration panel.

    Parameters
    ----------
    image_path:
        Path to the source illustration file.

    Returns
    -------
    Image.Image
        Page-sized illustration image.
    """

    with Image.open(image_path) as source_image:
        image = source_image.convert("RGBA")
        flattened = Image.new("RGBA", image.size, (255, 255, 255, 255))
        flattened.alpha_composite(image)
        return ImageOps.fit(
            flattened,
            (PAGE_WIDTH, PAGE_HEIGHT),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        ).convert("RGB")


def render_back_cover_page(
    back_cover: PageSpec,
    workspace: StoryWorkspace,
    background_color: tuple[int, int, int],
    text_color: tuple[int, int, int],
) -> Image.Image:
    """Render the back cover."""

    teaser = "\n\n".join(text.strip() for text in back_cover.text if text.strip())
    illustration = back_cover.illustration
    if illustration is None:
        return render_centered_text_page(
            text=teaser,
            background_color=background_color,
            text_color=text_color,
            error_message="The back-cover teaser does not fit on the page.",
        )

    page = render_illustration_page(workspace.directory / illustration.image_path)
    if illustration.text_mode == "embedded":
        return page
    return overlay_back_cover_text(page, teaser, text_color)


def overlay_back_cover_text(
    page: Image.Image,
    teaser: str,
    text_color: tuple[int, int, int],
) -> Image.Image:
    """Overlay teaser text onto a full-page back-cover illustration."""

    canvas = page.convert("RGBA")
    draw = ImageDraw.Draw(canvas, "RGBA")
    panel_top = round(PAGE_HEIGHT * 0.58)
    draw.rectangle(
        [(scale(TEXT_MARGIN_X) - scale(30), panel_top), (PAGE_WIDTH - scale(TEXT_MARGIN_X) + scale(30), PAGE_HEIGHT - scale(TEXT_MARGIN_Y) + scale(40))],
        fill=(255, 255, 255, 180),
    )
    draw_centered_text_block(
        draw=draw,
        text=teaser,
        box=(scale(TEXT_MARGIN_X), panel_top + scale(50), PAGE_WIDTH - scale(TEXT_MARGIN_X), PAGE_HEIGHT - scale(TEXT_MARGIN_Y)),
        font_sizes=[scale(fs) for fs in (BODY_FONT_SIZE, 54, 50, 46, 42)],
        line_spacing=scale(BODY_LINE_SPACING),
        text_color=text_color,
        bold=False,
        error_message="The back-cover teaser does not fit on the illustration overlay.",
    )
    return canvas.convert("RGB")


def render_illustrated_page(
    page: PageSpec | None,
    workspace: StoryWorkspace,
    background_color: tuple[int, int, int],
) -> Image.Image:
    """Render an illustrated page or a blank fallback."""

    if page is None or page.illustration is None:
        return render_blank_page(background_color)
    return render_illustration_page(workspace.directory / page.illustration.image_path)


def render_blank_page(background_color: tuple[int, int, int]) -> Image.Image:
    """Render a blank page."""

    return Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), background_color)


def render_centered_text_page(
    text: str,
    background_color: tuple[int, int, int],
    text_color: tuple[int, int, int],
    error_message: str,
) -> Image.Image:
    """Render a centered text page."""

    page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), background_color)
    draw = ImageDraw.Draw(page)
    draw_centered_text_block(
        draw=draw,
        text=text,
        box=(scale(TEXT_MARGIN_X), scale(TEXT_MARGIN_Y), PAGE_WIDTH - scale(TEXT_MARGIN_X), PAGE_HEIGHT - scale(TEXT_MARGIN_Y)),
        font_sizes=[scale(fs) for fs in (BODY_FONT_SIZE, 54, 50, 46, 42)],
        line_spacing=scale(BODY_LINE_SPACING),
        text_color=text_color,
        bold=False,
        error_message=error_message,
    )
    return page


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a serif font suitable for storybook pages.

    Parameters
    ----------
    size:
        Requested font size in pixels.
    bold:
        Whether to prefer a bold serif face.

    Returns
    -------
    ImageFont.FreeTypeFont
        Loaded font object.

    Raises
    ------
    SystemExit
        If no suitable serif font can be found on the host machine.
    """

    candidates = [
        Path("C:/Windows/Fonts/georgiab.ttf" if bold else "C:/Windows/Fonts/georgia.ttf"),
        Path("C:/Windows/Fonts/BASKVILL.ttf" if bold else "C:/Windows/Fonts/BASKVILI.ttf"),
        Path("C:/Windows/Fonts/timesbd.ttf" if bold else "C:/Windows/Fonts/times.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf"),
        Path("/System/Library/Fonts/Supplemental/Georgia Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Georgia.ttf"),
        Path("/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Times New Roman.ttf"),
    ]

    for candidate in candidates:
        if not candidate.is_file():
            continue
        try:
            return ImageFont.truetype(str(candidate), size=size)
        except OSError:
            continue

    raise SystemExit("Could not find a serif TrueType font required to render storybook pages.")


def wrap_text(text: str, draw: ImageDraw.ImageDraw, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Wrap story text into page-sized lines.

    Parameters
    ----------
    text:
        Input text to wrap.
    draw:
        Pillow drawing context used for measurements.
    font:
        Font used for width calculations.
    max_width:
        Maximum allowed line width in pixels.

    Returns
    -------
    list[str]
        Wrapped lines ready to render in order.

    Raises
    ------
    SystemExit
        If a single word cannot fit within the allowed width.
    """

    lines: list[str] = []
    paragraphs = [paragraph.strip() for paragraph in text.strip().splitlines()]
    for paragraph_index, paragraph in enumerate(paragraphs):
        if not paragraph:
            if lines and lines[-1]:
                lines.append("")
            continue

        current_line = ""
        for word in paragraph.split():
            candidate = word if not current_line else f"{current_line} {word}"
            candidate_bbox = draw.textbbox((0, 0), candidate, font=font)
            candidate_width = candidate_bbox[2] - candidate_bbox[0]
            if candidate_width <= max_width:
                current_line = candidate
                continue

            if not current_line:
                raise SystemExit(f"The word {word!r} is too wide to fit on a storybook page.")

            lines.append(current_line)
            current_line = word
            current_line_bbox = draw.textbbox((0, 0), current_line, font=font)
            current_line_width = current_line_bbox[2] - current_line_bbox[0]
            if current_line_width > max_width:
                raise SystemExit(f"The word {word!r} is too wide to fit on a storybook page.")

        if current_line:
            lines.append(current_line)

        if paragraph_index < len(paragraphs) - 1 and lines and lines[-1]:
            lines.append("")

    return lines


def draw_centered_text_block(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    font_sizes: Sequence[int],
    line_spacing: int,
    text_color: tuple[int, int, int],
    bold: bool,
    error_message: str,
) -> None:
    """Draw centered wrapped text that fits inside the provided box."""

    left, top, right, bottom = box
    available_width = right - left
    available_height = bottom - top

    for font_size in font_sizes:
        font = load_font(font_size, bold=bold)
        lines = wrap_text(text, draw, font, available_width)
        line_height = font.size + line_spacing
        text_height = len(lines) * line_height - line_spacing
        if text_height > available_height:
            continue

        y = top + ((available_height - text_height) // 2)
        for line in lines:
            if line:
                line_bbox = draw.textbbox((0, 0), line, font=font)
                line_width = line_bbox[2] - line_bbox[0]
                x = left + ((available_width - line_width) // 2)
                draw.text((x, y), line, fill=text_color, font=font)
            y += line_height
        return

    raise SystemExit(error_message)


def has_page_text_content(page: PageSpec | None) -> bool:
    """Return whether a page contains any visible text content."""

    return page is not None and any(text.strip() for text in page.text)


def build_page_document(title: str, image_href: str, image_alt: str) -> str:
    """Build a fixed-layout XHTML page wrapper around one rendered image.

    Parameters
    ----------
    title:
        Document title.
    image_href:
        Relative image path inside the EPUB package.
    image_alt:
        Alternative text for the page image.

    Returns
    -------
    str
        XHTML document string.
    """

    return dedent(
        f"""\
        <?xml version="1.0" encoding="utf-8"?>
        <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
          <head>
            <title>{escape(title)}</title>
            <meta name="viewport" content="width={PAGE_WIDTH}, height={PAGE_HEIGHT}"/>
            <link rel="stylesheet" type="text/css" href="../styles.css"/>
          </head>
          <body>
            <img class="page-image" src="{escape(image_href)}" alt="{escape(image_alt)}"/>
          </body>
        </html>
        """
    )


def build_stylesheet() -> str:
    """Build the shared stylesheet for all fixed-layout page wrappers.

    Returns
    -------
    str
        CSS stylesheet content.
    """

    return dedent(
        f"""\
        html,
        body {{
            margin: 0;
            padding: 0;
            width: {PAGE_WIDTH}px;
            height: {PAGE_HEIGHT}px;
        }}

        body {{
            overflow: hidden;
        }}

        .page-image {{
            display: block;
            width: {PAGE_WIDTH}px;
            height: {PAGE_HEIGHT}px;
        }}
        """
    )


def build_navigation_document(title: str, nav_links: list[str]) -> str:
    """Build the EPUB navigation document.

    Parameters
    ----------
    title:
        Story title.
    nav_links:
        Pre-rendered navigation list items.

    Returns
    -------
    str
        XHTML navigation document.
    """

    return dedent(
        f"""\
        <?xml version="1.0" encoding="utf-8"?>
        <html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en">
          <head>
            <title>{escape(title)}</title>
          </head>
          <body>
            <nav epub:type="toc" id="toc">
              <h1>{escape(title)}</h1>
              <ol>
                {' '.join(nav_links)}
              </ol>
            </nav>
          </body>
        </html>
        """
    )


def build_package_document(
        workspace: StoryWorkspace,
        storybook: Storybook,
        manifest_items: list[str],
        spine_items: list[str],
) -> str:
    """Build the EPUB package document.

    Parameters
    ----------
    workspace:
        Story workspace used to derive a stable identifier.
    storybook:
        Parsed storybook metadata.
    manifest_items:
        Pre-rendered manifest entries.
    spine_items:
        Pre-rendered spine entries.

    Returns
    -------
    str
        OPF package document.
    """

    identifier = f"urn:uuid:{uuid5(NAMESPACE_URL, f'librito:{workspace.story}:{storybook.title}')}"
    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return dedent(
        f"""\
        <?xml version="1.0" encoding="utf-8"?>
        <package
            xmlns="http://www.idpf.org/2007/opf"
            xmlns:dc="http://purl.org/dc/elements/1.1/"
            unique-identifier="book-id"
            version="3.0"
            prefix="dcterms: http://purl.org/dc/terms/ rendition: http://www.idpf.org/vocab/rendition/#">
          <metadata>
            <dc:identifier id="book-id">{escape(identifier)}</dc:identifier>
            <dc:title>{escape(storybook.title)}</dc:title>
            <dc:creator>{escape(storybook.author)}</dc:creator>
            <dc:language>und</dc:language>
            <meta property="dcterms:modified">{modified}</meta>
            <meta property="rendition:layout">pre-paginated</meta>
            <meta property="rendition:spread">both</meta>
          </metadata>
          <manifest>
            {' '.join(manifest_items)}
          </manifest>
          <spine>
            {' '.join(spine_items)}
          </spine>
        </package>
        """
    )


def build_container_document() -> str:
    """Build the EPUB container document.

    Returns
    -------
    str
        XML container document.
    """

    return dedent(
        """\
        <?xml version="1.0" encoding="utf-8"?>
        <container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
          <rootfiles>
            <rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/>
          </rootfiles>
        </container>
        """
    )


def write_epub_archive(staging_root: Path, output_path: Path) -> None:
    """Write the staged EPUB filesystem tree into the final ZIP archive.

    Parameters
    ----------
    staging_root:
        Root directory containing the staged EPUB files.
    output_path:
        Destination EPUB path.
    """

    with zipfile.ZipFile(output_path, mode="w") as archive:
        archive.write(
            staging_root / "mimetype",
            arcname="mimetype",
            compress_type=zipfile.ZIP_STORED,
        )
        for path in sorted(staging_root.rglob("*")):
            if path.is_dir() or path.name == "mimetype":
                continue
            archive.write(
                path,
                arcname=path.relative_to(staging_root).as_posix(),
                compress_type=zipfile.ZIP_DEFLATED,
            )


if __name__ == "__main__":
    raise SystemExit(main())
