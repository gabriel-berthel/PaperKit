# init_warmup.py

import logging
from functools import lru_cache
from pathlib import Path
import subprocess

log = logging.getLogger("init_warmup")
logging.basicConfig(level=logging.INFO)


# ----------------------------
# NLTK bootstrap
# ----------------------------
def ensure_nltk():
    import nltk

    resources = {
        "tokenizers/punkt": "punkt",
        "corpora/wordnet": "wordnet",
        "corpora/omw-1.4": "omw-1.4",
        "corpora/words": "words",
    }

    for path, name in resources.items():
        try:
            nltk.data.find(path)
        except LookupError:
            log.info(f"Downloading NLTK resource: {name}")
            nltk.download(name, quiet=True)

# ----------------------------
# Lazy cached models
# ----------------------------
@lru_cache(maxsize=1)
def get_embedding_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


@lru_cache(maxsize=1)
def get_reranker():
    from sentence_transformers import CrossEncoder
    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


@lru_cache(maxsize=1)
def get_bart_pipeline():
    from transformers import pipeline
    return pipeline("summarization", model="facebook/bart-large-cnn")


@lru_cache(maxsize=1)
def get_summarizer():
    from sumy.summarizers.lsa import LsaSummarizer
    from sumy.nlp.stemmers import Stemmer
    from sumy.utils import get_stop_words

    summarizer = LsaSummarizer(Stemmer("english"))
    summarizer.stop_words = get_stop_words("english")
    return summarizer


# ----------------------------
# Heavy model singletons
# ----------------------------
@lru_cache(maxsize=1)
def init_surya():
    from surya.inference import SuryaInferenceManager
    from surya.recognition import RecognitionPredictor
    
    manager = SuryaInferenceManager()
    predictor = RecognitionPredictor(manager)
    return predictor

@lru_cache(maxsize=1)
def init_gliner():
    from gliner2 import GLiNER2
    return GLiNER2.from_pretrained("fastino/gliner2-base-v1")

@lru_cache(maxsize=1)
def init_spacy():
    from spacy.lang.en import English
    return English()

@lru_cache(maxsize=1)
def init_tooling():
    import language_tool_python
    return language_tool_python.LanguageTool("en-US")

@lru_cache(maxsize=1)
def init_segmentation():
    import pysbd
    return pysbd.Segmenter(language="en", clean=False, doc_type=None)

@lru_cache(maxsize=1)
def init_wordset():
    from nltk.corpus import words
    return set(words.words())

# ----------------------------
# Docling pre-download
# ----------------------------
def download_docling_models():
    """
    Pre-download Docling models using CLI tool.
    Safe to run at startup.
    """
    try:
        log.info("Downloading Docling models via CLI...")

        subprocess.run(
            ["docling-tools", "models", "download"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        log.info("Docling models download complete.")

    except FileNotFoundError:
        log.warning("docling-tools not found in PATH. Skipping download step.")

    except subprocess.CalledProcessError as e:
        log.error("Docling model download failed:")
        log.error(e.stderr)


# ----------------------------
# Piper
# ----------------------------  
def init_piper(voice):
    """
    Warm up Piper TTS voice models.
    """
    from piper import PiperVoiceà
    model_path = Path(f"voices/{voice}.onnx")
    config_path = Path(f"voices/{voice}.onnx.json")
    return PiperVoice.load(model_path, config_path=config_path)

def init_llama32():
    import ollama
    ollama.pull("llama3.2")
    

# ----------------------------
# Master initializer
# ----------------------------
def boostrap_project_librairies():
    """
    Call this once at startup to:
    - download NLTK data
    - warm up ML models
    - preload heavy singletons
    """

    log.info("Starting global initialization...")

    ensure_nltk()

    # light-ish first
    _ = init_wordset()
    _ = init_segmentation()

    # ML models (heavy)
    _ = get_embedding_model()
    _ = get_reranker()
    _ = get_bart_pipeline()
    _ = get_summarizer()

    _ = init_gliner()
    _ = init_spacy()
    _ = init_tooling()

    # Surya OCR pipeline
    _ = init_surya()
    
    # All the docling model
    download_docling_models()
    
    # Dowloading llama3.2
    init_llama32()

    log.info("Initialization complete.")

boostrap_project_librairies()