

from pathlib import Path

from p6t.persistance.db import db_push
from p6t.model.normalized_document import NormalizedDocument
import pickle


from p6t.model.parsed_document import ParsedDocument
from p6t.normalizing.normalized_document_builder import NormalizedDocumentBuilder

def normalize_document(parsed_document: ParsedDocument) -> NormalizedDocument:
    print("Building Normalized")
    normalized_document = NormalizedDocumentBuilder(parsed_document).build()
    return normalized_document

def normalize_and_push(parsed_document: ParsedDocument) -> NormalizedDocument:
    """
    Normalize ParsedDocument into a NormalizedDocument and save it as a pickle file.
    """

    print("Normalizing document content")
    normalized_document: NormalizedDocument = normalize_document(parsed_document)
    file_path = db_push(parsed_document.source_document.pdf_hash, 'normalizing', normalized_document)

    return file_path