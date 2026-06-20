

from p6t.persistance.db import push
from p6t.model.parsed_document import ParsedDocument
from p6t.model.source_document import SourceDocument
from p6t.parsing.docling_converter import DoclingConverter
from p6t.parsing.ocr import SuryaLatexOCR
from docling_core.types.doc import DoclingDocument
import pickle
from pathlib import Path
import os
import logging

SURYA_BATCH_SIZE = int(os.getenv("SURYA_BATCH_SIZE", "8"))

logging.basicConfig(level=logging.INFO)

converter = DoclingConverter()
surya = SuryaLatexOCR()

def parse_document(file_path) -> ParsedDocument:
    """
    1: Creates source document representation (saving every page)
    2: Parse PDF with docling (no OCR, Formula + Code Enrichment)
    3: Re-OCR textual elements using surya OCR (will inline maths elements)
    """

    print("Creating source document")
    source_document = SourceDocument(file_path)

    print("Parsing document w/ docling")
    docling_document: DoclingDocument = converter.parse(file_path)

    items = []

    print("Collecting textual element crops")
    for element, _ in docling_document.iterate_items():
        if element.label in ["caption", "text", "list_item", "footnote"]:
            bbox = element.prov[0].bbox
            page_no = element.prov[0].page_no

            crop = source_document.resize_max_2048(source_document.crop(page_no, bbox))
            items.append((element, crop))

    print("Running surya OCR on textual elements")
    for i in range(0, len(items), SURYA_BATCH_SIZE):
        batch = items[i:i + SURYA_BATCH_SIZE]
        crops = [crop for _, crop in batch]

        results = surya.run_single_block(crops)

        # Mutating elements
        for (element, _), text in zip(batch, results):
            element.text = text

    return ParsedDocument(source_document, docling_document)

def parse_and_push(pdf_path):
    parsed_document: ParsedDocument = parse_document(pdf_path)
    push(parsed_document.source_document.pdf_hash, 'parsing', parsed_document)

def parse_and_pickle(pdf_path, output_path, output_name):
    """
    Parses a PDF into a ParsedDocument (Docling Document + SourceDocument) and saves it as a pickle file.
    """

    print("Parsing document + OCR")
    parsed_document: ParsedDocument = parse_document(pdf_path)

    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    file_path = output_path / f"{output_name}.pkl"

    print(f"Saving pickled document to {file_path}")

    with open(file_path, "wb") as f:
        pickle.dump(parsed_document, f, protocol=pickle.HIGHEST_PROTOCOL)

    print("Done")

    return file_path