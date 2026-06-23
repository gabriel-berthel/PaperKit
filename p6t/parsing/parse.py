

from p6t.persistance.db import db_get, db_push
from p6t.model.parsed_document import ParsedDocument
from p6t.model.source_document import SourceDocument
from p6t.parsing.docling_converter import DoclingConverter
from p6t.parsing.ocr import SuryaLatexOCR
from docling_core.types.doc import DoclingDocument

converter = DoclingConverter()
surya = SuryaLatexOCR()

def parse_document(file_path, batch_size=8, skip_ocr=False) -> ParsedDocument:
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
    if not skip_ocr:
        print("Running surya OCR on textual elements")
        for element, _ in docling_document.iterate_items():
            if element.label in ["caption", "text", "list_item", "footnote"]:
                bbox = element.prov[0].bbox
                page_no = element.prov[0].page_no

                # crop = source_document.resize_max_2048(source_document.crop(page_no, bbox))
                print(f"Re-OCRing {element.self_ref}")
                crop = source_document.crop(page_no, bbox)
                result = surya.run_blocks([crop])[0]
                
                if result:
                    element.text = result
                    
        print("Running surya OCR on formulas")
        for element, _ in docling_document.iterate_items():
            if element.label in ["formula"]:
                bbox = element.prov[0].bbox
                page_no = element.prov[0].page_no

                # crop = source_document.resize_max_2048(source_document.crop(page_no, bbox))
                print(f"Re-OCRing {element.self_ref}")
                crop = source_document.crop(page_no, bbox)
                result = surya.run_formulas([crop])[0]
                
                if result:
                    element.text = result
                

    return ParsedDocument(source_document, docling_document)

def parse_and_push(pdf_path, batch_size=8, skip_ocr=False):
    parsed_document: ParsedDocument = parse_document(pdf_path, batch_size, skip_ocr)
    db_push(parsed_document.source_document.pdf_hash, 'parsing', parsed_document)
    return parsed_document