import argparse
from pathlib import Path

from p6t.bundle.bundle import export_document
from p6t.model.normalized_document import NormalizedDocument
from p6t.model.parsed_document import ParsedDocument
from p6t.normalizing.normalize import normalize_and_push
from p6t.parsing.parse import parse_and_push
from p6t.persistance.db import db_get
from p6t.serialize.serialize import serialize_html, serialize_markdown, serialize_text
import subprocess

from p6t.tools.bootsrap import boostrap_project_librairies

def cmd_register(args):
    pdf_path = Path(args.pdf)

    parsed_document: ParsedDocument = db_get(pdf_path, "parsing")

    if parsed_document and not args.force:
        answer = input(
            f"'{pdf_path.name}' has already been parsed. Reparse? [y/N]: "
        ).strip().lower()

        if answer in {"y", "yes"}:
            print("Parsing...")
            parsed_document = parse_and_push(pdf_path, args.batch, args.skip_ocr)
        else:
            print("Using existing parsed document.")

    else:
        if parsed_document and args.force:
            print("Reparsing (--force)...")
        else:
            print("Parsing...")

        parsed_document = parse_and_push(pdf_path, args.batch, args.skip_ocr)

    print("Normalizing...")
    normalized_document = normalize_and_push(parsed_document)

    print(
        f"Registered '{pdf_path.name}' "
        f"({len(normalized_document.pages)} pages)"
    )
    
def cmd_serialize(args):
    pdf_path = Path(args.pdf)

    normalized_document: NormalizedDocument = db_get(pdf_path, "normalizing")

    if not normalized_document:
        print(
            f"Document '{pdf_path.name}' has not been registered yet. "
            "Run 'p6t register <pdf>' first."
        )
        return 1

    if args.format == "md":
        output = serialize_markdown(normalized_document)
    elif args.format == "html":
        output = serialize_html(normalized_document)
    else:
        output = serialize_text(normalized_document)

    print(output)
    return 0

def cmd_bundle(args):
    pdf_path = Path(args.pdf)

    normalized_document: NormalizedDocument = db_get(pdf_path, "normalizing")
    parsed_document: ParsedDocument = db_get(pdf_path, "parsing")
    
    if not normalized_document:
        print(
            f"Document '{pdf_path.name}' has not been registered yet. "
            "Run 'p6t register <pdf>' first."
        )
        return 1

    print("Exporting bundle...")
    export_document(normalized_document, f"./db/bundles/{parsed_document.source_document.pdf_hash}")

    print(f"Bundle exported for '{pdf_path.name}'")
    return 0


def cmd_serve(args):
    pdf_path = Path(args.pdf)

    parsed_document: ParsedDocument = db_get(pdf_path, "parsing")

    if not parsed_document:
        print(
            f"Document '{pdf_path.name}' has not been parsed. "
            "Run 'p6t register <pdf>' first."
        )
        return 1

    normalized_document: NormalizedDocument = db_get(
        pdf_path,
        "normalizing"
    )

    if not normalized_document:
        print(
            f"Document '{pdf_path.name}' has not been normalized. "
            "Run 'p6t register <pdf>' first."
        )
        return 1

    bundle_dir = Path(
        f"./db/bundles/{parsed_document.source_document.pdf_hash}"
    )

    if not bundle_dir.exists():
        print(
            f"Bundle does not exist for '{pdf_path.name}'. "
            "Run 'p6t bundle <pdf>' first."
        )
        return 1

    print(f"Serving bundle: {bundle_dir}")

    static_server = subprocess.Popen(
        ["python", "-m", "http.server", "8000"],
        cwd=bundle_dir,
    )

    api_server = subprocess.Popen(
        [
            "uvicorn",
            "p6t.tools.api:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8080",
        ]
    )

    print("Static server: http://localhost:8000")
    print("API server:    http://localhost:8080")
    print("Press Ctrl+C to stop.")

    try:
        static_server.wait()
        api_server.wait()
    except KeyboardInterrupt:
        print("\nStopping servers...")
        static_server.terminate()
        api_server.terminate()

    return 0

def cmd_init(args):
    print("Bootstrapping project libraries...")

    boostrap_project_librairies()

    print("Initialization complete.")
    return 0

def main():
    parser = argparse.ArgumentParser(prog="p6t")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Register
    parser = argparse.ArgumentParser(prog="p6t")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Register
    register_parser = subparsers.add_parser(
        "register",
        help="Register document: parse and normalize the pdf"
    )

    register_parser.add_argument(
        "pdf",
        help="Path to the PDF file"
    )

    register_parser.add_argument(
        "--force",
        action="store_true",
        help="Reparse the document without prompting"
    )

    # NEW: skip OCR flag (default False)
    register_parser.add_argument(
        "--skip-ocr",
        action="store_true",
        help="Skip OCR step (default: False)"
    )

    # batch size (default 8)
    register_parser.add_argument(
        "--batch",
        type=int,
        default=8,
        help="Batch size for processing (default: 8)"
    )

    register_parser.set_defaults(func=cmd_register)

    # Serialize
    serialize_parser = subparsers.add_parser(
        "serialize",
        help="Export pdf as a text file"
    )
    serialize_parser.add_argument(
        "pdf",
        help="Path to the PDF file"
    )
    serialize_parser.add_argument(
        "--format",
        "-f",
        choices=["md", "html", "text"],
        required=True,
        help="Output format"
    )
    serialize_parser.set_defaults(func=cmd_serialize)
    
    # Bundler
    bundle_parser = subparsers.add_parser(
        "bundle",
        help="Bundle the document into the interactive webpage"
    )
    bundle_parser.add_argument(
        "pdf",
        help="Path to the PDF file"
    )
    bundle_parser.set_defaults(func=cmd_bundle)
    
    # Serving the document
    serve_parser = subparsers.add_parser(
        "serve",
        help="Serve interactive webpage"
    )
    serve_parser.add_argument(
        "pdf",
        help="Path to the PDF file"
    )
    serve_parser.set_defaults(func=cmd_serve)
        
    # Bootrapping
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize the project environment"
    )
    init_parser.set_defaults(func=cmd_init)
        
    args = parser.parse_args()
    raise SystemExit(args.func(args))

if __name__ == "__main__":
    main()