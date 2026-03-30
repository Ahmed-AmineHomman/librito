"""Assemble a fixed-layout EPUB storybook from scene texts and illustrations."""

from __future__ import annotations

import sys
import shutil
import zipfile
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
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
from librito.models import Storybook
from librito.workspace import StoryWorkspace

logger = logging.getLogger(__name__)

PAGE_WIDTH = 1600
PAGE_HEIGHT = 2560
TEXT_MARGIN_X = 170
TEXT_MARGIN_Y = 220
BODY_FONT_SIZE = 58
BODY_LINE_SPACING = 22
TITLE_FONT_SIZE = 126
TITLE_LINE_SPACING = 28
DEFAULT_BACKGROUND_COLOR = "#f6f1e8"
DEFAULT_TEXT_COLOR = "#1d1a17"


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
            Assemble a fixed-layout EPUB storybook from a segmented story.

            The command validates that every scene has reader-facing text and an
            existing illustration, then renders a minimalist two-page spread per
            scene: left page for text, right page for the illustration.
            """
        ).strip(),
        epilog=dedent(
            """
            Behavior:
              - reads ``database/<story>/story.json``
              - validates the title, scene texts, and generated illustrations
              - renders a text-only cover plus one text page and one image page per scene
              - writes the final EPUB to ``database/<story>/story.epub``

            Layout:
              - cover: text only
              - each scene: exactly 2 pages
              - left page: rendered text on a flat configurable background
              - right page: full-page illustration

            Examples:
              python helpers/assemble_storybook.py --story sir_turnip
              python helpers/assemble_storybook.py --story sir_turnip --background-color "#f4efe6"
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
        "--background-color",
        default=DEFAULT_BACKGROUND_COLOR,
        help=f"Solid background color for the cover and text pages (default: {DEFAULT_BACKGROUND_COLOR}).",
    )
    parser.add_argument(
        "--text-color",
        default=DEFAULT_TEXT_COLOR,
        help=f"Text color for the cover and text pages (default: {DEFAULT_TEXT_COLOR}).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the storybook assembly entrypoint.

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
    background_color = ImageColor.getrgb(arguments.background_color)
    text_color = ImageColor.getrgb(arguments.text_color)

    logger.info("Starting assembly pipeline for story '%s'.", workspace.story)
    story_path = workspace.require_storybook_file()
    logger.info("Loading storybook from %s.", story_path)
    storybook = load_storybook(story_path)
    validate_storybook(storybook, workspace)

    output_path = workspace.book_file
    output_path.parent.mkdir(parents=True, exist_ok=True)

    staging_root = workspace.directory / "_storybook_assembly_tmp"
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

        logger.info("Rendering cover and scene pages.")
        render_cover_page(storybook.title, background_color, text_color).save(
            images_directory / "cover.png"
        )
        (pages_directory / "cover.xhtml").write_text(
            build_page_document(
                title=storybook.title,
                image_href="../images/cover.png",
                image_alt=f"Cover for {storybook.title}",
            ),
            encoding="utf-8",
        )

        manifest_items = [
            '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
            '<item id="stylesheet" href="styles.css" media-type="text/css"/>',
            '<item id="cover-image" href="images/cover.png" media-type="image/png" properties="cover-image"/>',
            '<item id="cover-page" href="pages/cover.xhtml" media-type="application/xhtml+xml"/>',
        ]
        spine_items = ['<itemref idref="cover-page"/>']
        nav_links = ['<li><a href="pages/cover.xhtml">Cover</a></li>']

        for scene_number, scene in enumerate(storybook.scenes, start=1):
            logger.info(
                "Rendering spread for scene %d/%d (%s).",
                scene_number,
                len(storybook.scenes),
                scene.label,
            )
            text_image_name = f"scene-{scene_number:03d}-text.png"
            illustration_image_name = f"scene-{scene_number:03d}-illustration.png"
            text_page_name = f"scene-{scene_number:03d}-text.xhtml"
            illustration_page_name = f"scene-{scene_number:03d}-illustration.xhtml"

            render_scene_text_page(
                scene.label,
                scene.text,
                background_color,
                text_color,
            ).save(
                images_directory / text_image_name
            )
            render_illustration_page(workspace.directory / scene.image_path).save(
                images_directory / illustration_image_name
            )

            (pages_directory / text_page_name).write_text(
                build_page_document(
                    title=f"Scene {scene_number}",
                    image_href=f"../images/{text_image_name}",
                    image_alt=f"Scene {scene_number} text",
                ),
                encoding="utf-8",
            )
            (pages_directory / illustration_page_name).write_text(
                build_page_document(
                    title=f"Scene {scene_number} illustration",
                    image_href=f"../images/{illustration_image_name}",
                    image_alt=f"Scene {scene_number} illustration",
                ),
                encoding="utf-8",
            )

            manifest_items.extend(
                [
                    f'<item id="scene-{scene_number:03d}-text-image" href="images/{text_image_name}" media-type="image/png"/>',
                    f'<item id="scene-{scene_number:03d}-illustration-image" href="images/{illustration_image_name}" media-type="image/png"/>',
                    f'<item id="scene-{scene_number:03d}-text-page" href="pages/{text_page_name}" media-type="application/xhtml+xml"/>',
                    f'<item id="scene-{scene_number:03d}-illustration-page" href="pages/{illustration_page_name}" media-type="application/xhtml+xml"/>',
                ]
            )
            spine_items.extend(
                [
                    f'<itemref idref="scene-{scene_number:03d}-text-page" properties="page-spread-left"/>',
                    f'<itemref idref="scene-{scene_number:03d}-illustration-page" properties="page-spread-right"/>',
                ]
            )
            nav_links.append(
                f'<li><a href="pages/{text_page_name}">Scene {scene_number}</a></li>'
            )

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
    if not storybook.scenes:
        raise SystemExit("The storybook does not contain any scenes to assemble.")

    for scene_number, scene in enumerate(storybook.scenes, start=1):
        if not scene.text.strip():
            raise SystemExit(f"Scene {scene_number} ({scene.label}) has empty text.")
        if not scene.image_path.strip():
            raise SystemExit(f"Scene {scene_number} ({scene.label}) is missing image_path.")

        image_path = workspace.directory / scene.image_path
        if not image_path.is_file():
            raise SystemExit(
                f"Scene {scene_number} ({scene.label}) is missing its illustration file: {image_path}"
            )

        try:
            with Image.open(image_path) as image:
                image.verify()
        except Exception as error:
            raise SystemExit(
                f"Scene {scene_number} ({scene.label}) illustration could not be opened: {image_path}"
            ) from error


def render_cover_page(title: str, background_color: tuple[int, int, int], text_color: tuple[int, int, int]) -> Image.Image:
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
    available_width = PAGE_WIDTH - (TEXT_MARGIN_X * 2)
    available_height = PAGE_HEIGHT - (TEXT_MARGIN_Y * 2)

    for font_size in (TITLE_FONT_SIZE, 112, 100, 90, 82, 74):
        font = load_font(font_size, bold=True)
        lines = wrap_text(title, draw, font, available_width)
        line_height = font.size + TITLE_LINE_SPACING
        text_height = len(lines) * line_height - TITLE_LINE_SPACING
        if text_height > available_height:
            continue

        y = TEXT_MARGIN_Y + ((available_height - text_height) // 2)
        for line in lines:
            line_bbox = draw.textbbox((0, 0), line, font=font)
            line_width = line_bbox[2] - line_bbox[0]
            x = (PAGE_WIDTH - line_width) // 2
            draw.text((x, y), line, fill=text_color, font=font)
            y += line_height
        return page

    raise SystemExit("The story title does not fit on the cover page.")


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
    font = load_font(BODY_FONT_SIZE)
    available_width = PAGE_WIDTH - (TEXT_MARGIN_X * 2)
    available_height = PAGE_HEIGHT - (TEXT_MARGIN_Y * 2)
    lines = wrap_text(text, draw, font, available_width)
    line_height = BODY_FONT_SIZE + BODY_LINE_SPACING
    text_height = len(lines) * line_height - BODY_LINE_SPACING
    if text_height > available_height:
        raise SystemExit(
            f"Scene {scene_label!r} text does not fit on its single left page."
        )

    y = TEXT_MARGIN_Y + ((available_height - text_height) // 2)
    for line in lines:
        if line:
            draw.text((TEXT_MARGIN_X, y), line, fill=text_color, font=font)
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
