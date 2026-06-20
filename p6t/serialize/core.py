

import pickle
import base64
import html
from p6t.model.dto.ir_nodes import IRCode, IRFormula, IRHeader, IRListItem, IRParagraph, IRFigure, IRTable
from p6t.model.normalized_document import NormalizedDocument


def flatten_elements(normalized_document: NormalizedDocument):
    
    items = []
    
    refs = {f"{e.label} {e.number}": e for e in normalized_document.tables + normalized_document.figures if e.label and e.number}
    footnotes = {e.identifier:e for e in normalized_document.footnotes if e.identifier}
    
    items.append(IRHeader(normalized_document.document_title))
    for section in normalized_document.tree.flat():
        
        items.append(IRHeader(section.full_title, level=2))
        
        for item in section.items:
            
            if isinstance(item, IRHeader):
                item.level = 3
                
            items.append(item)
            
            lower_txt = item.text.lower()
            if isinstance(item, IRParagraph|IRListItem):
                
                # Adding footnotes as paragraphs
                for identifier in footnotes.keys():
                    if f"footnote {identifier}" in lower_txt:
                        items.append(IRParagraph(f'footnote {identifier}: {footnotes[identifier].text}'))
                        del footnotes[identifier]
                
                # Adding medias on first appearance.
                for text_ref in refs.keys():
                    if text_ref in lower_txt:
                        items.append(refs[text_ref])
                        del refs[text_ref]
                
                        
    return items
            
def _image_to_data_uri(image_bytes, mime="image/png"):
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def serialize_html(ir_nodes):
    parts = [
        "<!DOCTYPE html>",
        "<html>",
        "<body>",
    ]

    for item in ir_nodes:
        if isinstance(item, IRParagraph):
            parts.append(f"<p>{html.escape(item.text)}</p>")

        elif isinstance(item, IRListItem):
            parts.append(f"<li>{html.escape(item.text)}</li>")

        elif isinstance(item, IRCode):
            parts.append(
                f"<pre><code>{html.escape(item.text)}</code></pre>"
            )

        elif isinstance(item, IRFormula):
            parts.append(
                f"<div class='formula'>{html.escape(item.text)}</div>"
            )

        elif isinstance(item, IRHeader):
            parts.append(f"<h{item.level}>{html.escape(item.text)}</h{item.level}>")

        elif isinstance(item, (IRTable, IRFigure)):
            src = _image_to_data_uri(item.image)

            parts.append("<figure>")
            parts.append(f"<img src='{src}' />")

            if item.caption:
                parts.append(
                    f"<figcaption>{html.escape(item.caption)}</figcaption>"
                )

            parts.append("</figure>")

    parts.extend([
        "</body>",
        "</html>",
    ])

    return "\n".join(parts)

def serialize_markdown(ir_nodes):
    parts = []

    for item in ir_nodes:
        if isinstance(item, IRParagraph):
            parts.append(item.text)
            parts.append("")

        elif isinstance(item, IRListItem):
            parts.append(f"- {item.text}")

        elif isinstance(item, IRCode):
            parts.append("```")
            parts.append(item.text)
            parts.append("```")
            parts.append("")

        elif isinstance(item, IRFormula):
            parts.append(f"$$\n{item.text}\n$$")
            parts.append("")

        elif isinstance(item, IRHeader):
            parts.append(f"{"#" * item.level} {item.text}")
            parts.append("")

        elif isinstance(item, (IRTable, IRFigure)):
            parts.append(f"![{item.caption}](embedded-image)")
            parts.append("")

            if item.caption:
                parts.append(f"*{item.caption}*")
                parts.append("")

    return "\n".join(parts)

def serialize_text(ir_nodes):
    parts = []

    for item in ir_nodes:
        if isinstance(item, IRParagraph):
            parts.append(item.text)

        elif isinstance(item, IRListItem):
            parts.append(f"• {item.text}")

        elif isinstance(item, IRCode):
            parts.append(item.text)

        elif isinstance(item, IRFormula):
            parts.append(item.text)

        elif isinstance(item, IRHeader):
            
            if item.level == 1:
                parts.append(item.text.upper())
                parts.append("=" * len(item.text))
            elif item.level == 2:
                parts.append(item.text.upper())
                parts.append("-" * len(item.text))
            else:
                parts.append(item.text.title())
                parts.append("-" * len(item.text))

        elif isinstance(item, (IRTable, IRFigure)):
            
            if item.caption:
                parts.append(f"[item.label]: {item.caption}")
            else:
                parts.append(f"[{item.label}]")

        parts.append("")

    return "\n".join(parts)