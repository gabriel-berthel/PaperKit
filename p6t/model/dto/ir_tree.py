
import re
from typing import List, Optional

from p6t.model.dto.ir_interfaces import IRTextNode


class IRTree:
    
    _id_counter = 0  # class variable (shared)
    
    def __init__(self, items, number_raw, number_parts, title, level = 0, pseudo_section=False):
        self.items: Optional[List[IRTextNode]] = items
        self.number_raw: Optional[str] = number_raw
        self.number_parts: Optional[List[int]] = number_parts
        self.title: Optional[str] = title
        self.level: int = level
        self.children: List["IRTree"] = []
        self.id:int = type(self)._id_counter 
        self.parent: "IRTree" = None
        
        type(self)._id_counter += 1
    
    @property
    def full_title(self):
        return f"[{self.number_raw}] {self.title}" if self.number_raw else self.title
    
    @staticmethod
    def build(sections) -> "IRTree":
        
        @staticmethod
        def split_numbering(text: str):
            match = re.match(r'^(\d+(?:\.\d+)*)\s+(.*)', text)
            if match:
                return match.group(1), match.group(2)
            return None, text
        
        root = IRTree(items=None, number_raw=None,
                           number_parts=None, title=None, level=0)
        
        stack = [root]
        for raw in sections:
            number_raw, title = split_numbering(raw.text)
            number_parts = [int(n) for n in number_raw.split(".")] if number_raw else None
            level = len(number_parts) if number_parts else 1
                
            node = IRTree(
                items=raw.items,
                number_raw=number_raw,
                number_parts=number_parts, # ex : 2 5 3
                title=title,
                level=level
            )

            while stack[-1].level >= level:
                stack.pop()

            node.parent = stack[-1]  
            stack[-1].children.append(node)
            stack.append(node)
        
        return root
    
    def flat(self, root: "IRTree" = None) -> list["IRTree"]:
        
        if not root:
            return self.flat(self)
        
        result = []

        # Root is a convenient placeholder.
        if root.level == 0:
            for c in root.children:
                result.extend(IRTree.flat(c))
            return result

        result.append(root)

        # Recurse into children
        for c in root.children:
            result.extend(IRTree.flat(c))

        return result