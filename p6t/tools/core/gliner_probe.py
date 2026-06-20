from spacy.lang.en import English
import torch

from p6t.tools.bootsrap import init_gliner

gliner_model = init_gliner()


nlp = English()

def is_valid_span(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < 3:
        return False
    doc = nlp(stripped)
    if all(token.is_stop for token in doc):
        return False
    return True

def gliner_probe(text: str, targets: list[str]) -> dict[str, list[str]]:
    clean_targets = [t.replace(' ', '_') for t in targets]
    
    with torch.inference_mode():
        result = gliner_model.extract_entities(text, clean_targets).get('entities', {})

    matches: dict[str, list[str]] = {t: [] for t in targets}
    for clean, original in zip(clean_targets, targets):
        values = result.get(clean, [])
        matches[original].extend(v for v in values if is_valid_span(v))

    return matches