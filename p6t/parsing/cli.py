import os
import argparse

from p6t.parsing.parse import parse_and_pickle

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path")
    parser.add_argument("output_path")
    parser.add_argument("--name", default="output")

    args = parser.parse_args()

    parse_and_pickle(
        pdf_path=args.pdf_path,
        output_path=args.output_path,
        output_name=args.name
    )

if __name__ == "__main__":
    os.environ["SURYA_INFERENCE_KEEP_ALIVE"] = "1"
    main()