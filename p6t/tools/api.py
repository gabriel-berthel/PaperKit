import io
import re
import unicodedata
import wave

from fastapi import APIRouter, Request, Response

from p6t.tools.bootsrap import init_piper
from p6t.tools.core import gliner_probe
from p6t.tools.core.llm import llm_explain_term, llm_simple_task, llm_simplify_text
from p6t.tools.utils.model import EntityProbe, TermInContextRequest, TextRequest, TextResponse
from p6t.tools.core.summary import single_paragraph_summury_pipeline
from p6t.tools.utils.utils import chunk_paragraphs
from p6t.tools.core.wikipedia import wikipedia_best_match
from p6t.tools.core.wordnet import get_wordnet_definition_in_context, word_in_wordnet
from p6t.tools.conf import settings

from contextlib import asynccontextmanager

from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.voice = init_piper(settings.piper_voice)
    yield
    app.state.voice = None

app = FastAPI(lifespan=lifespan)

router = APIRouter(prefix="/api")
app.include_router(router)


# ---------- TTS ---------- 
@router.post("/tts")
async def tts(request: Request, payload: TextRequest):
    if request.app.state.voice is None:
        return Response(status_code=503, content="Voice model not loaded")

    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as wav:
        request.app.state.voice.synthesize_wav(payload.text, wav)

    buffer.seek(0)

    return Response(content=buffer.read(), media_type="audio/wav")


# ---------- Gliner Probe ---------- 
@router.post("/entity/probe")
def probe_gliner(payload: EntityProbe) -> dict[str, list[str]]:
    paragraphs = [p.strip() for p in payload.text.split("\n") if p.strip()]
    chunks = chunk_paragraphs(paragraphs)

    matches = {target: [] for target in payload.targets}

    for paragraph in chunks:
        found = gliner_probe(paragraph, payload.targets)
        for target, spans in found.items():
            matches[target].extend(spans)

    return {k: list(set(v)) for k, v in matches.items()}



# ---------- What is it ---------- 
@router.post("/whatItIs")
async def whatisit_term(payload: TermInContextRequest) -> TextResponse:
    term = payload.term
    context = payload.context

    candidate_definition = ""

    try:
        if term.islower() and word_in_wordnet(term):
            candidate_definition = get_wordnet_definition_in_context(context, term)
        else:
            candidate_definition = await wikipedia_best_match(term, context)
    except Exception:
        candidate_definition = ""

    result = await llm_explain_term(term, context, candidate_definition)

    output = result["output"]
    if result.get("corrected"):
        output = f"(LLM corrected): {output}"

    return TextResponse(text=output)



# ---------- Summary ---------- 
@router.post("/summarize")
def build_overview(payload: TextRequest) -> TextResponse:
    return TextResponse(text=single_paragraph_summury_pipeline(payload.text))



# ---------- Simplifiers ---------- 
async def _simplify(text: str, instruction: str) -> str:
    out = await llm_simple_task(text, instruction)

    # fallback for non-ascii code/text
    if not out:
        clean = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        out = await llm_simple_task(clean, instruction)

    return re.sub(r"_(\w+)", r" sub \1", out)


@router.post("/simplify/expert")
async def simplify_text_expert(payload: TextRequest) -> TextResponse:
    return TextResponse(text=await llm_simplify_text(payload.text, level="graduate"))


@router.post("/simplify/student")
async def simplify_text_student(payload: TextRequest) -> TextResponse:
    return TextResponse(text=await llm_simplify_text(payload.text, level="student"))


@router.post("/simplify/maths")
async def simplify_maths(payload: TextRequest) -> TextResponse:
    instruction = (
        "Rewrite all mathematical expressions, variables, Greek letters, symbols, "
        "operators, equations, and notation as plain spoken English. "
        "Do not explain or solve. Output only text."
    )
    return TextResponse(text=await _simplify(payload.text, instruction))


@router.post("/simplify/wording")
async def simplify_wording(payload: TextRequest) -> TextResponse:
    return TextResponse(
        text=await llm_simple_task(payload.text, "Rewrite in simpler words without changing structure.")
    )


@router.post("/simplify/caption")
async def simplify_caption_content(payload: TextRequest) -> TextResponse:
    return TextResponse(
        text=await llm_simple_task(payload.text, "Summarize caption text for readability.")
    )


@router.post("/simplify/code")
async def simplify_code(payload: TextRequest) -> TextResponse:
    instruction = "Briefly describe what this code block does in natural spoken English, as if explaining it out loud to someone listening."

    simplified = await llm_simple_task(payload.text, instruction)

    if not simplified:
        text = unicodedata.normalize("NFKD", payload.text).encode("ascii", "ignore").decode("ascii")
        simplified = await llm_simple_task(text, instruction)

    return TextResponse(text=simplified)