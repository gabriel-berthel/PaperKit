from dataclasses import dataclass
from p6t.model.dto.ir_interfaces import IRMediaAnchor, IRTextAnchor
from p6t.model.dto.ir_tree import IRTree
    
@dataclass(frozen=True)
class NormalizedDocument:    
    document_title: str
    tree: IRTree
    
    footnotes: list[IRTextAnchor]
    tables: list[IRMediaAnchor]
    figures: list[IRMediaAnchor]
    
    references: list[str]