
from abc import ABC
import re
from typing import ClassVar

## Base Nodes
class IRNode(ABC):
    pass

class IRContainerNode(IRNode):
    def __init__(self, items):
        self.items: list[IRNode] = items
        
class IRTextNode(IRNode):
    def __init__(self, text):
        self.text = text 

## Base Anchors

class IRTextAnchor():
    
    def __init__(self, identifier, text):
        self.identifier = identifier   
        self.text = text
        
class IRMediaAnchor():
    
    _counter: ClassVar[int] = 0
    
    def extract_caption(self, text: str):
        
        CAPTION_HEADER_RE = re.compile(r"""
            ^\s*
            (figure|table)
            \s+
            (\d+)
            \s*[:.\-–]?
        """, re.IGNORECASE | re.VERBOSE)
        
        m = CAPTION_HEADER_RE.match(text)
        
        if not m:
            return None

        label = m.group(1).lower()
        number = int(m.group(2))
        
        return {'label': label.lower(), 'number': number}

    def __init__(self, img, caption):
        self.img = img
        self.caption = caption
        
        caption_extract = self.extract_caption(self.caption)
        
        if caption_extract:
            self.label  = caption_extract['label']
            self.number = caption_extract['number']
        else:
            self.label = caption
            self.number = ""

        self.media_ref = IRMediaAnchor._counter
        IRMediaAnchor._counter += 1 