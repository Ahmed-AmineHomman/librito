"""
Return the texts of the specified scenes of the segmentation.
"""
from argparse import ArgumentParser, Namespace


def load_parameters() -> Namespace:
    parser = ArgumentParser(
        description="Returns the attributes (text and/or prompts) of the specified scenes"
    )
    parser.add_argument(
        "--storybook",
        type=str,
        required=True,
        help="Label of the storybook",
    )
    parser.add_argument(
        "--labels",
        type=str,
        nargs="+",
        required=True,
        help="Scene labels",
    )
    parser.add_argument(
        "--attributes",
        choices=["text", "prompt"],
        nargs="+",
        required=True,
        help="Attributes to fetch (scene text or prompt)",
    )
    parser.add_argument(
        "--expand",
        action="store_true",
        help="Expand prompt by replacing anchors with their values (only applicable for prompt attributes)",
    )
    return parser.parse_args()


def main():
    args = load_parameters()

    # TODO: implement script
    raise NotImplementedError()


if __name__ == "__main__":
    main()