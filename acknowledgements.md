# Acknowledgements

PaperKit (`p6t`) is built on top of the work of many open source projects.
Thank you to the authors and maintainers of the following.

## PDF parsing and OCR

- [Docling](https://github.com/DS4SD/docling), document parsing and layout analysis
- [Surya OCR](https://github.com/VikParuchuri/surya), OCR and math inlining
- [pdf2image](https://github.com/Belval/pdf2image), PDF to image conversion
- [pytesseract](https://github.com/madmaze/pytesseract), Python wrapper for Tesseract OCR
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract), the underlying OCR engine

## Text processing and normalization

- [pysbd](https://github.com/nipunsadvilkar/pySBD), sentence boundary segmentation
- [deepmultilingualpunctuation](https://github.com/oliverguhr/deepmultilingualpunctuation), punctuation restoration
- [NLTK](https://www.nltk.org/), natural language toolkit
- [language_tool_python](https://github.com/jxmorris12/language_tool_python), grammar and style checking
- [pylatexenc](https://github.com/phfaist/pylatexenc), LaTeX parsing and conversion

## Entity recognition, embeddings, and summarization

- [GLiNER2](https://github.com/fastino-ai/GLiNER2), generalist named entity recognition
- [spaCy](https://spacy.io/), natural language processing
- [Sumy](https://github.com/miso-belica/sumy), text summarization
- [Sentence Transformers](https://www.sbert.net/), sentence and text embeddings
- [scikit-learn](https://scikit-learn.org/), machine learning utilities

## Text to speech

- [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M), open weight text to speech model
- [kokoro-tts](https://github.com/nazdridoy/kokoro-tts), Kokoro CLI wrapper

## Web and tooling

- [FastAPI](https://fastapi.tiangolo.com/), web API framework
- [Uvicorn](https://www.uvicorn.org/), ASGI server
- [curl_cffi](https://github.com/yifeikong/curl_cffi), HTTP client with browser impersonation
- [Jinja2](https://jinja.palletsprojects.com/), templating engine

If a dependency is missing from this list, please open an issue or a pull
request so it can be added.