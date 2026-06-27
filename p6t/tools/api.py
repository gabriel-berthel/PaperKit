import os
import subprocess
import tempfile
import unicodedata
from pathlib import Path

from fastapi import APIRouter, Response
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from p6t.tools.core.gliner_probe import gliner_probe
from p6t.tools.core.llm import llm_explain_term, llm_simple_task, llm_simplify_text
from p6t.tools.core.summary import single_paragraph_summary_pipeline
from p6t.tools.core.wikipedia import wikipedia_best_match
from p6t.tools.core.wordnet import get_wordnet_definition_in_context, word_in_wordnet
from p6t.tools.utils.model import EntityProbe, TermInContextRequest, TextRequest, TextResponse
from p6t.tools.utils.utils import chunk_paragraphs

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


router = APIRouter(prefix="/api")
app.include_router(router)

# ---------- Paper ---------- 


app.mount(
    "/js",
    StaticFiles(directory=f"{os.environ["BASE_FOLDER"]}/js"),
    name="js",
)

app.mount(
    "/css",
    StaticFiles(directory=f"{os.environ["BASE_FOLDER"]}/css"),
    name="css",
)

app.mount(
    "/media",
    StaticFiles(directory=f"{os.environ["BASE_FOLDER"]}/media"),
    name="media",
)

@app.get("/")
async def root():
    return FileResponse(
        f"{os.environ['BASE_FOLDER']}/index.html"
    )
    

# ---------- TTS ---------- 

def synthesize_wav(text: str) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name

    try:
        subprocess.run(
            ["kokoro-tts", "-", wav_path, "--voice", "am_michael"],
            input=text,
            text=True,
            check=True,
        )

        return Path(wav_path).read_bytes()

    finally:
        Path(wav_path).unlink(missing_ok=True)

@router.post("/tts")
async def tts(payload: TextRequest):
    wav_bytes = synthesize_wav(payload.text)

    return Response(
        content=wav_bytes,
        media_type="audio/wav",
    )

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
async def search_what_the_term_is(payload: TermInContextRequest) -> TextResponse:
    term = payload.term
    context = payload.context

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
    return TextResponse(text=single_paragraph_summary_pipeline(payload.text))



# ---------- Simplifies ----------
@router.post("/simplify/expert")
async def simplify_text_expert(payload: TextRequest) -> TextResponse:
    return TextResponse(text=await llm_simplify_text(payload.text, level="graduate"))


@router.post("/simplify/student")
async def simplify_text_student(payload: TextRequest) -> TextResponse:
    return TextResponse(text=await llm_simplify_text(payload.text, level="student"))


@router.post("/simplify/wording")
async def simplify_wording(payload: TextRequest) -> TextResponse:
    return TextResponse(
        text=await llm_simple_task(payload.text, "Rewrite in simpler words without changing structure.")
    )
    
@router.post("/simplify/formula")
async def simplify_caption_content(payload: TextRequest) -> TextResponse:
    response = TextResponse(
        text=await llm_simple_task(
            payload.text, 
            "Convert this mathematical expression into the way it would be naturally spoken aloud in English"
        )
    )
    
    response.text.replace("_", " sub ")
    return response


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