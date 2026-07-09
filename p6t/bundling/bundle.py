import json
import os
import re
import shutil
from pathlib import Path
from unicodedata import normalize

from jinja2 import Environment, FileSystemLoader

from p6t.model.normalized_document import NormalizedDocument
from p6t.serializing.core import flatten_elements
from p6t.serializing.serialize import serialize_json
from importlib.resources import files

def load_index_template():
    templates_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(templates_dir)))
    index = env.get_template("index.jinja")
    return index

index = load_index_template()


# Copied from
# https://leancrew.com/all-this/2023/08/slugify-slight-return/
def slugify(text):
    '''Make an ASCII slug of text'''
    
    # Make lower case and delete apostrophes from contractions
    slug = re.sub(r"(\w)['’](\w)", r"\1\2", text.lower())
    
    # Convert runs of non-characters to single hyphens, stripping from ends
    slug = re.sub(r'[\W_]+', '-', slug).strip('-')
    
    # Replace a few special characters that normalize doesn't handle
    specials = {'æ':'ae', 'ß':'ss', 'ø':'o'}
    for s, r in specials.items():
        slug = slug.replace(s, r)
    
    # Normalize the non-ASCII text
    slug = normalize('NFKD', slug).encode('ascii', 'ignore').decode()
    
    # Return the transformed string
    return slug

def get_section_elements(normalized_document: NormalizedDocument):
    return json.loads(
        serialize_json(flatten_elements(normalized_document, resolve_refs=False))
    ) 

def get_and_save_refs(normalized_document: NormalizedDocument, media_path):
    
    refs = {}

    # Filling media refs.
    print("Saving medias")
    for media in normalized_document.tables + normalized_document.figures:
        pil_image = media.img
        caption = media.caption
        ref = f"{media.label}:{media.number}" if media.label and media.number else None
        
        if ref:
            filename = f"{ref}.png"
            filepath = media_path / filename
            pil_image.save(filepath, format="png")
            refs[ref] = caption

    # Filling footnote refs
    print("Extracting footnotes")
    for footnote in normalized_document.footnotes:
        caption = footnote.text
        ref = f"footnote:{footnote.identifier}"
        
        if footnote.identifier:
            refs[ref] = caption

    return refs

def bundle_static_files(output_path):
    # Copying js into bundle
    print("Bunding scripts")
    js_src = Path("p6t/bundling/templates/js")
    js_dst = output_path / "js"
    shutil.copytree(js_src, js_dst, dirs_exist_ok=True)

    # Copying css into bundle
    print("Bunding styles")
    css_src = Path("p6t/bundling/templates/css")
    css_dst = output_path / "css"
    shutil.copytree(css_src, css_dst, dirs_exist_ok=True)
    
def export_document(normalized_document: NormalizedDocument, output_folder):
    
    index = load_index_template()
    section_elements = get_section_elements(normalized_document)
    
    output_path = Path(os.path.join(output_folder))
    output_path.mkdir(parents=True, exist_ok=True)
    
    media_path = output_path / "media"
    media_path.mkdir(parents=True, exist_ok=True)
    refs = get_and_save_refs(normalized_document, media_path)

    # Save and rendering index
    print("Serializing document content")
    with open( output_path / "index.html", "w", encoding="utf-8") as f:
        f.write(index.render(
            title=normalized_document.document_title,
            elements=section_elements,
            refs=refs,
            references=normalized_document.references,
            slug=slugify(normalized_document.document_title)
        ))

    # Bundling JS / CSS files
    bundle_static_files(output_path)
    
    return output_path
