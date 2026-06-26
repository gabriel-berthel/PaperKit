import re

from PIL.Image import Image as PILImage
from typing_extensions import final

from p6t.model.dto.ir_interfaces import IRContainerNode, IRMediaAnchor, IRTextAnchor, IRTextNode


@final
class IRSection(IRContainerNode):
    def __init__(self, text: str):
        super().__init__([])
        header_text = text.strip().rstrip('.')
        self.text = header_text
        
    @staticmethod
    def build(element):   
        return IRSection(element.text)

## Textual Nodes
@final
class IRParagraph(IRTextNode):
    def __init__(self, text: str):
        super().__init__(text)
        
    @staticmethod
    def build(element):
        return IRParagraph(element.text)

@final        
class IRListItem(IRTextNode):
    def __init__(self, text: str):
        super().__init__(text)
        
    @staticmethod
    def build(element):
        return IRListItem(element.text)

@final             
class IRFormula(IRTextNode):
    def __init__(self, text: str, orig:str):
        super().__init__(text)
        self.orig = orig
        
    @staticmethod
    def build(element):
        return IRFormula(element.text if element.text else element.orig, element.orig)

@final            
class IRHeader(IRTextNode):
    def __init__(self, text: str, level = 1):
        header_text = text.strip().rstrip('.')
        super().__init__(header_text)
        self.level = level
    
    @staticmethod
    def build(element):
        return IRHeader(element.text)
    
@final            
class IRCode(IRTextNode):
    def __init__(self, text: str):
        super().__init__(text)
    
    @staticmethod
    def build(element):
        return IRCode(element.text)
    
## Anchor Node

@final      
class IRFootnote(IRTextAnchor):
    def __init__(self, identifier, text: str):
        super().__init__(identifier, text)
    
    @staticmethod
    def build(element):
            
        def parse_footnote(text: str):
            text = text.strip()
            symbol_match = re.match(r'^([^\w\s\d]+|\d+)', text)
            if symbol_match:
                footnote_id = symbol_match.group(1).strip()
                content = text[symbol_match.end():].lstrip(':').strip()
                content = text[symbol_match.end():].lstrip('.').strip()
                return footnote_id, content
            
            return None, text
            
        footnote_id, content = parse_footnote(element.text)
        return IRFootnote(footnote_id, content)

@final      
class IRTable(IRMediaAnchor):
    def __init__(self,caption: str, img:PILImage):
            super().__init__(img=img, caption=caption)
    
    @staticmethod
    def build(caption, image):
        return IRTable(caption, image)

@final      
class IRFigure(IRMediaAnchor):
    def __init__(self,caption: str, img:PILImage):
        super().__init__(img=img, caption=caption)
        
    @staticmethod
    def build(caption, image):
        return IRFigure(caption, image)
            