
import base64
from io import BytesIO

from p6t.model.dto.ir_nodes import IRHeader, IRListItem, IRParagraph
from p6t.model.normalized_document import NormalizedDocument


def flatten_elements(normalized_document: NormalizedDocument, resolve_refs=True):
    
    items = []
    
    refs = {f"{e.label} {e.number}": e for e in normalized_document.tables + normalized_document.figures if e.label and e.number}
    footnotes = {e.identifier:e for e in normalized_document.footnotes if e.identifier}
    
    seen = []
    items.append(IRHeader(normalized_document.document_title))
    for section in normalized_document.tree.flat():
        
        items.append(IRHeader(section.full_title, level=2))
        
        for item in section.items:
            
            if isinstance(item, IRHeader):
                item.level = 3
                
            items.append(item)
            
            lower_txt = item.text.lower()
            
            if resolve_refs and isinstance(item, IRParagraph|IRListItem):
                
                # Adding footnotes as paragraphs
                for identifier in footnotes.keys():
                    if f"footnote {identifier}" in lower_txt:
                        items.append(IRParagraph(f'footnote {identifier}: {footnotes[identifier].text}'))
                
                # Adding medias on first appearance.
                for text_ref in refs.keys():
                    if text_ref in lower_txt and text_ref not in seen:
                        items.append(refs[text_ref])
                        seen.append(text_ref)

                    
    return items
            
def image_to_data_uri(img):
    buffer = BytesIO()
    img.save(buffer, format="png")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:{"image/png"};base64,{encoded}"
