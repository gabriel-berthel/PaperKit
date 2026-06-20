import os
from pydantic import BaseModel

class Settings(BaseModel):
    llm_url: str = "http://localhost:11434/api/chat"
    llm_model: str = "llama3.2:3b"
    piper_voice: str = "en_US-lessac-high.onnx"

settings = Settings(
    llm_url=os.getenv("LLM_URL", "http://localhost:11434/api/chat"),
    llm_model=os.getenv("LLM_MODEL", "llama3.2:3b"),
    piper_voice=os.getenv("PIPER_VOICE", "en_US-lessac-high.onnx"),
)