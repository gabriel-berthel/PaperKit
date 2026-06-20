import argparse
import pickle
from pathlib import Path

from p6t.serialize.core import flatten_elements
from p6t.serialize.serialize import (
    serialize_json,
    serialize_markdown,
    serialize_html,
    serialize_text,
)

SERIALIZERS = {
    "json": serialize_json,
    "md": serialize_markdown,
    "html": serialize_html,
    "text": serialize_text,
}

def main():
    parser = argparse.ArgumentParser(
        prog="serialize",
        description="Serialize a pickled NormalizedDocument."
    )

    parser.add_argument(
        "format",
        choices=SERIALIZERS.keys(),
        help="Output format"
    )

    parser.add_argument(
        "pickle_path",
        help="Path to pickled NormalizedDocument"
    )

    parser.add_argument(
        "output",
        nargs="?",
        help="Output file path (optional)"
    )

    args = parser.parse_args()

    with open(args.pickle_path, "rb") as f:
        document = pickle.load(f)

    ir_nodes = flatten_elements(document)

    content = SERIALIZERS[args.format](ir_nodes)

    if args.output:
        output_path = Path(args.output)
    else:
        suffixes = {
            "json": ".json",
            "md": ".md",
            "html": ".html",
            "text": ".txt",
        }

        output_path = (
            Path(args.pickle_path).with_suffix("")
            .with_suffix(suffixes[args.format])
        )

    output_path.write_text(content, encoding="utf-8")
    print(f"Written: {output_path}")


if __name__ == "__main__":
    main()