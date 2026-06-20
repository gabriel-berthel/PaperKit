

import json
import html
from p6t.model.dto.ir_nodes import IRCode, IRFormula, IRHeader, IRListItem, IRParagraph, IRFigure, IRTable
from p6t.serialize.core import image_to_data_uri

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
            src = image_to_data_uri(item.image)

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

 
def serialize_json(ir_nodes):
    items = []

    label_map = {
        'IRHeader': 'heading',
        'IRCode': 'code',
        'IRFormula': 'formula',
        'IRListItem': 'bullet',
        'IRParagraph': 'paragraph',
        'IRFootnote': 'footnote',
        'IRTable': 'table',
        'IRFigure': 'figure'
    }

    for item in ir_nodes:
        items.append({
            "type": label_map[item.__class__.__name__],
            "content": getattr(item, "text", None)
                      or getattr(item, "caption", None)
                      or "",
            "level": getattr(item, "level", 0) 
        })

    return json.dumps(items, ensure_ascii=False, indent=2)