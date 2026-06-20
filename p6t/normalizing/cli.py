from pathlib import Path
import argparse
import pickle

from p6t.model.parsed_document import ParsedDocument
from p6t.normalizing.normalize import normalize_and_pickle

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("parsed_doc_pkl")
    parser.add_argument("output_path")
    parser.add_argument("--name", default="parsed_doc_output")

    args = parser.parse_args()

    with open(args.parsed_doc_pkl, 'rb') as f:
        parsed_document: ParsedDocument = pickle.load(f)

    normalize_and_pickle(
        parsed_document,
        args.output_path,
        args.name
    )

if __name__ == "__main__":
    main()