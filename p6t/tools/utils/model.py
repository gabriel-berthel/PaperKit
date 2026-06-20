from annotated_types import T
from pydantic import BaseModel

class TextRequest(BaseModel):
    text: str
    
class EntityProbe(BaseModel):
  text: str
  targets: list[str]    

class TermInContextRequest(BaseModel):
    term: str
    context: str
    
    