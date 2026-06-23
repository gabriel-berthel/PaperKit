from p6t.model.parsed_document import ParsedDocument
from p6t.persistance.db import db_get


document: ParsedDocument = db_get("2.pdf", "parsing")

for e, _ in document.docling_document.iterate_items():
    if hasattr(e, 'text'):
        print(e.text)