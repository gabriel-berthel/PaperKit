# PaperKit (p6t)

Making science more accessible.

`p6t` is a CLI toolkit for turning PDF documents (e.g. scientific papers) into
read-oriented, interactive documents, with OCR, math inlining, sentence
segmentation, text normalization, and more built in.

It's meant as an alternative to tools like NotebookLM, but built around a
different idea: instead of handing you an AI-generated summary, `p6t` puts
you at the source of every transformation decision. Nothing is summarized
or interpreted on your behalf. The goal is that you build your own
understanding of the document, not that a model builds it for you.

The project is open source and runs entirely locally, so your documents
never leave your machine. It's designed to run on a single modern CPU
with 16GB of RAM. No GPU is required, though on that kind of hardware
you should expect processing to be slow.

Right now this is more of a proof of concept than a finished product.
The transformation tasks currently rely on general-purpose, off the
shelf models. Future versions will include models fine-tuned
specifically for each transformation task, which should meaningfully
improve results. The project is also deterministic: given the same
input, you'll get the same output every time.
 

## Requirements

- Python >= 3.12
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed on your machine
  (required by `pytesseract`)
- [Poppler](https://poppler.freedesktop.org/) installed on your machine
  (required by `pdf2image`)
- OpenJDK installed on your machine (required by `language_tool_python`)

## Installation

Install directly from the Git repository using pip:

```bash
pip install git+https://github.com/gabriel-berthel/PaperKit.git
```

For local development (editable install):

```bash
git clone https://github.com/gabriel-berthel/PaperKit.git
cd <your-repo>
pip install -e .
```

> **Note:** This project pins specific versions of `transformers`
> (`4.56.1`) and `deepmultilingualpunctuation` (`1.0.1`+) to avoid
> dependency conflicts between the OCR/NER stack (`docling`, `surya-ocr`,
> `gliner2`, `sentence_transformers`) and the punctuation restoration
> model. If you hit `TypeError` or `ImportError` issues related to
> `transformers`, make sure these pins are respected in your environment.

## Lazy model loading

No models are downloaded at install time. Everything is lazy loaded on
first use, so `pip install` stays fast and you only pull down what you
actually run. This includes:

- Llama 3.2 (used for math inlining / VLM tasks)
- Docling's parsing and layout models
- Kokoro TTS voice packs
- NLTK corpora (e.g. `words`)
- Any other models pulled in by `surya-ocr`, `gliner2`, or
  `sentence_transformers`

The first time you run a command that needs a given model, expect a
one time download. Subsequent runs use the cached weights. Make sure
you have network access and disk space available the first time you
run `p6t register` on a fresh machine.

If you want to pre warm the cache instead of downloading on demand,
run a `p6t register` against a small test PDF right after install.

## Usage

The CLI is installed as the `p6t` command.

### Register a document

Parses and normalizes a PDF, storing the results locally so subsequent
commands can reuse them.

```bash
p6t register path/to/paper.pdf
```

Options:

| Flag           | Description                                              | Default |
|----------------|-----------------------------------------------------------|---------|
| `--force`      | Reparse the document without prompting                    | off     |
| `--skip-ocr`   | Skip the OCR step                                          | off     |
| `--batch N`    | Batch size used during processing                          | `8`     |

If the document has already been parsed, you'll be prompted to reparse
unless `--force` is passed.

### Serialize a document

Exports a registered document as a readable file (Markdown, HTML, or
plain text). The output is written to the current directory.

```bash
p6t serialize path/to/paper.pdf --format md
```

Options:

| Flag              | Description                          |
|-------------------|---------------------------------------|
| `--format`, `-f`  | Output format: `md`, `html`, or `txt` (required) |

This is the intended entry point for feeding a document into a RAG
(retrieval augmented generation) pipeline. The output is clean,
normalized text or markdown that's ready to chunk and embed, without
the layout noise, OCR artifacts, or formatting clutter of the raw PDF.

The document must be registered first (`p6t register`).

### Bundle a document

Exports the normalized document into an interactive web bundle.

```bash
p6t bundle path/to/paper.pdf
```

The document must be registered first (`p6t register`).

### Serve a document

Starts a local API server for the interactive bundle.

```bash
p6t serve path/to/paper.pdf
```

The document must be registered and bundled first
(`p6t register` then `p6t bundle`). Once running:

```
API server: http://localhost:8080
```

Press `Ctrl+C` to stop the server.

## Typical workflow

```bash
p6t register path/to/paper.pdf
p6t bundle path/to/paper.pdf
p6t serve path/to/paper.pdf
```

## License

This project is open source. See /licenses for full license details.