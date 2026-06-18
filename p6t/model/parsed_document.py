
from dataclasses import dataclass

from docling_core.types.doc import DoclingDocument
from model.source_document import SourceDocument

@dataclass
class ParsedDocument:
    source_document: SourceDocument
    docling_document: DoclingDocument