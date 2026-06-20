import argparse
import pickle
from pathlib import Path

from p6t.bundle.bundle import export_document

def main():
    parser = argparse.ArgumentParser(
        prog="bundle",
        description="Bundle document for rendering."
    )
    
    parser.add_argument(
        "pickle_path",
        help="Path to pickled NormalizedDocument pkl"
    )

    args = parser.parse_args()

    with open(args.pickle_path, "rb") as f:
        document = pickle.load(f)

    output_path = export_document(document, ".")
    
    print(f"Written: {output_path}")


if __name__ == "__main__":
    main()