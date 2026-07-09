# init_warmup.py
import os
import subprocess
import time
from functools import lru_cache
from pathlib import Path
import requests

def download_if_missing(url: str, filename: str) -> None:
    if os.path.exists(filename):
        print(f"{filename} already exists, skipping")
        return

    print(f"↓ Downloading {filename}...")
    response = requests.get(url, stream=True)
    response.raise_for_status() 

    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            
def ensure_kokoro_voices():
    print("Ensuring TTS voices")
    
    download_if_missing(
        "https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx",
        "kokoro-v1.0.onnx"
    )   
    
    download_if_missing(
        "https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin",
        "voices-v1.0.bin"
    )     

# ----------------------------
# NLTK components
# ----------------------------
def ensure_nltk():
    print(f"Ensuring NLTK resources")
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
            nltk.download(name, quiet=True)

# ----------------------------
# Lazy cached models
# ----------------------------
@lru_cache(maxsize=1)
def get_embedding_model():
    print("Init: all-MiniLM-L6-v2")
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


@lru_cache(maxsize=1)
def get_reranker():
    print("Init: cross-encoder/ms-marco-MiniLM-L-6-v2")
    from sentence_transformers import CrossEncoder
    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


@lru_cache(maxsize=1)
def get_bart_pipeline():
    print("Init: facebook/bart-large-cnn")
    from transformers import pipeline
    return pipeline("summarization", model="facebook/bart-large-cnn")


@lru_cache(maxsize=1)
def get_summarizer():
    print("Init: Sumy/LSA-Summurizer")
    from sumy.summarizers.lsa import LsaSummarizer
    from sumy.nlp.stemmers import Stemmer
    from sumy.utils import get_stop_words

    summarizer = LsaSummarizer(Stemmer("english"))
    summarizer.stop_words = get_stop_words("english")
    return summarizer


@lru_cache(maxsize=1)
def init_surya():
    print("Init: SuryaOCR")
    from surya.inference import SuryaInferenceManager
    from surya.recognition import RecognitionPredictor
    
    manager = SuryaInferenceManager()
    predictor = RecognitionPredictor(manager)
    return predictor

@lru_cache(maxsize=1)
def init_gliner():
    print("Init: fastino/gliner2-base-v1")
    from gliner2 import GLiNER2
    model = GLiNER2.from_pretrained("fastino/gliner2-base-v1")
    return model
    
@lru_cache(maxsize=1)
def init_spacy():
    print("Init: Spacy")
    from spacy.lang.en import English
    return English()

@lru_cache(maxsize=1)
def init_tooling():
    print("Init: LanguageToolPython")
    import language_tool_python
    return language_tool_python.LanguageTool("en-US")

@lru_cache(maxsize=1)
def init_segmentation():
    print("Init: pysbd")
    import pysbd
    return pysbd.Segmenter(language="en", clean=False, doc_type=None)

@lru_cache(maxsize=1)
def init_wordset():
    from nltk.corpus import words
    return set(words.words())


def download_docling_models():
    """
    Pre-download Docling models using CLI tool.
    Safe to run at startup.
    """
    try:
        print("Downloading Docling models via CLI...")

        subprocess.run(
            ["docling-tools", "models", "download"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        print("Docling models download complete.")

    except FileNotFoundError:
        print("docling-tools not found in PATH. Skipping download step.")

    except subprocess.CalledProcessError as e:
        print("Docling model download failed:")
        print(e.stderr)


def init_llama32():
    # Start Ollama in the background
    import ollama
    print("Starting ollama")
    
    process = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Give the server a moment to start
    time.sleep(2)

    ollama.pull("llama3.2")

    return process
    