from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.wsd import lesk

from p6t.tools.lazy_loading import ensure_nltk

ensure_nltk()

lemmatizer = WordNetLemmatizer()

def word_in_wordnet(word):
    word = word.lower()
    lemma = lemmatizer.lemmatize(word)
    return bool(wn.synsets(lemma))

def get_wordnet_definition_in_context(full_text, target_word):
    """
    Determines the most appropriate WordNet sense (definition) of a target word
    given its surrounding context.

    1. Extracts the local context by selecting sentences surrounding the target word.
    2. Applies the Lesk algorithm for word sense disambiguation using the context
       to select the WordNet sense with the highest overlap.
    """
    
    # Segment text into clean sentences
    sentences = sent_tokenize(full_text)
    
    # Locate the sentence containing the target word
    target_idx = -1
    for idx, sentence in enumerate(sentences):
        tokens = [t.lower() for t in word_tokenize(sentence)]
        if target_word.lower() in tokens:
            target_idx = idx
            break
            
    if target_idx == -1:
        return None
    
    # Context window (sentence before, sentence w/ target, sentence after)
    start_idx = max(0, target_idx - 1)
    end_idx = min(len(sentences), target_idx + 2)
    context_window = sentences[start_idx:end_idx]
    optimized_context_str = " ".join(context_window)
    
    # Lemmatization / Tokenization
    context_tokens = word_tokenize(optimized_context_str.lower())
    lemmatized_tokens = [lemmatizer.lemmatize(t) for t in context_tokens]
    
    # Using Lesk to find best definition.
    best_synset = lesk(lemmatized_tokens, target_word.lower())
    
    if best_synset:
        return best_synset.definition()

    return None