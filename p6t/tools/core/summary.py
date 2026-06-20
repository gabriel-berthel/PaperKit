import unicodedata

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer

from p6t.bootsrap import get_bart_pipeline, get_summarizer

MAX_BART_CTX = 1024


def summarize(text:str):
    """
    Summarizing using BART. Assuming ctx limit is accounted for upstream.
    """
    
    tokenizer = get_bart_pipeline().tokenizer
    input_token_count = len(tokenizer.encode(text))
     
    return get_bart_pipeline()(
        text,
        do_sample=False,
        max_length=max(int(input_token_count * 0.8), 30),
        min_length=min(int(input_token_count * 0.4), 15),
        num_beams=4,
        length_penalty=1.5,
        no_repeat_ngram_size=3,
        early_stopping=True
    )

def single_paragraph_summury_pipeline(text: str) -> dict:
    """
    Summarizing using BART. The handles token count greater than ctx by trimming input content using LSA. 
    """
    
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    
    bart_pipeline = get_bart_pipeline()
    tokenizer = bart_pipeline.tokenizer
    input_token_count = len(tokenizer.encode(text))

    # if more tokens than context can handle
    # building an extractive summary using LSA up to MAX_BART_CTX
    if input_token_count > MAX_BART_CTX:
        text = lsa_filter_sentences(text, tokenizer, MAX_BART_CTX)
    
    result = summarize(text)
    return result[0]["summary_text"]

def lsa_filter_sentences(text: str, tokenizer, target_no_token = MAX_BART_CTX) -> dict:
    """
    Builds an extractive summary using LSA:
    - Sentences are ranked
    - Summuary length is determined by target_no_token
    """
    
    parser = PlaintextParser.from_string(text, Tokenizer("english"))

    sentence_count = len(parser.document.sentences)

    ranked = list(
        get_summarizer()(parser.document, sentence_count)
    )

    selected, current_tokens = [], 0

    for sent in ranked:
        sent_text = str(sent)
        no_tokens = len(tokenizer.encode(sent_text))

        if current_tokens + no_tokens > target_no_token:
            break

        selected.append(sent)
        current_tokens += no_tokens

    selected_set = set(selected)

    lsa_summary = " ".join(
        str(s)
        for s in parser.document.sentences
        if s in selected_set
    )
    
    return lsa_summary
