
import re

import language_tool_python
import pysbd
from deepmultilingualpunctuation import PunctuationModel
from nltk.corpus import words

from p6t.normalizing.text_cleaner import TextCleaner
from p6t.tools.lazy_loading import ensure_nltk

tool = language_tool_python.LanguageTool('en-US')
seg = pysbd.Segmenter(language="en", clean=False, doc_type=None)

ensure_nltk()
word_set = set(words.words())
punctuation_model = PunctuationModel()


STRUCTURE = {
    'table',
    'figure',
    'section',
    'subsection',
    'appendix',
    'chapter',
    'theorem',
    'lemma',
    'corollary',
    'proposition',
    'definition',
    'proof',
    'algorithm',
    'equation',
    'example',
    'remark'
}

SENTENCE_MARKERS = {
    # Articles
    'a', 'an', 'the',

    # Personal pronouns
    'i', 'we', 'you', 'they', 'he', 'she', 'it',

    # Object pronouns
    'me', 'us', 'him', 'her', 'them',

    # Possessive determiners
    'my', 'our', 'your', 'their', 'his', 'its',

    # Possessive pronouns
    'mine', 'ours', 'yours', 'theirs', 'hers',

    # Demonstratives
    'this', 'that', 'these', 'those',

    # Reflexives
    'myself', 'yourself', 'himself', 'herself',
    'itself', 'ourselves', 'yourselves', 'themselves',

    # Indefinite pronouns
    'someone', 'somebody', 'something',
    'anyone', 'anybody', 'anything',
    'everyone', 'everybody', 'everything',
    'none', 'nothing', 'each', 'either', 'neither',

    # Relative / interrogative
    'who', 'whom', 'whose', 'which', 'what',
    'where', 'when', 'why',

    # Subordinating conjunctions
    'if', 'unless', 'whether',
    'provided', 'assuming',
    'because', 'since', 'as',
    'although', 'though', 'whereas',
    'while', 'before', 'after',
    'until', 'once',

    # Conjunctive adverbs / discourse markers
    'however', 'therefore', 'thus',
    'hence', 'consequently', 'accordingly',
    'moreover', 'furthermore', 'additionally',
    'besides', 'indeed', 'likewise',
    'nevertheless', 'nonetheless',
    'yet', 'instead', 'conversely', 'otherwise',
    'similarly', 'analogously',

    # Sequencing
    'first', 'second', 'third',
    'next', 'then', 'subsequently',
    'meanwhile', 'previously', 'finally',

    # Academic exposition
    'specifically', 'namely',
    'particularly', 'notably',
    'importantly',

    # Reference words
    'above', 'below',
    'following', 'preceding',
    'aforementioned',
    'former', 'latter',
    'respectively',
    'herein', 'therein',
    
    # Quantifiers
    'most', 'many', 'much', 'more', 'less', 'fewer',
    'some', 'several', 'various', 'numerous',
    'few', 'little', 'all', 'both',
    
    # Usual starts:
    'in', 'for', 'one', 'on', 'to'
}

class TextFixer:

    @staticmethod
    def split_sentences(text):
        return seg.segment(text)
    
    @staticmethod
    def has_known_word(text):
        """
        Verify the text contains at least 1 english word.
        """
        
        if not text:
            return False
        
        if re.match(r'\$(.*?)\$', text):
            return True
        
        # No alphanum
        if not [character for character in list(text) if character.isalpha()]:
            return False
        
        # not looking up non alpha words (tho set operations are already fast)
        for w in text.split():
            w = w.lower()
            if len(w) >= 2 and w.isalpha() and w in word_set:
                return True
            
        return False

    @staticmethod
    def is_heading(sentence):
        """
        Assumes sentence boundaries have been fixed upstream.
        If headers are being misclassified, the heuristics here are the likely culprit.
        """
   
        # Missed paragraph continuation
        if sentence and sentence[0].islower() or not sentence[0].isalnum():
            return False
            
        # Known non-header patterns. Regex would catch more but risks introducing
        # more bugs than it solves. these cases are rare enough that explicit checks are safer.
        if "et al" in sentence or "keywords:" in sentence.lower():
            return False
        
        header_words = TextCleaner.remove_punct(sentence)

        # Likely a header (not text marker)
        if len(header_words.split()) <= 10 and not TextFixer.first_word_in(sentence, SENTENCE_MARKERS | STRUCTURE):
            return True
        
        return False

    @staticmethod
    def extract_heading(text: str) -> tuple[str | None, str]:
        """
        Detect heading within paragraph.
        """

        # Paragraph might be the heading.
        sentences = TextFixer.split_sentences(text)
        if len(sentences) <= 1 and TextFixer.is_heading(text): 
            return text, None
        
        left = sentences[0]
        if TextFixer.is_heading(left): 
            right = text.split(".", maxsplit=1)[1]
            return left, right.strip()
        
        return None, text
    
    @staticmethod
    def remove_punct(text):
        return re.sub(r"(?<!\d)[.,;:!?'](?!\d)","",text) 
   
    @staticmethod
    def find_candidate_period(text):
        """
        Deepmultilingualpunctuation is slow but produces good results for punctuation restoration.
        It can't infer headers though, so we locate an initial boundary, then scan adjacent words
        for a better split: headings tend to capitalize most words, which serves as the signal.
        
        Note: if boundary lookup fails, missing pre-sub rule might be the culprit.
        
        This function either returns a single word (the candidate boundary) or None.
        """
        
        # This broke deep punctuation a handful of times
        # Removing these from the search avoid reliance on heuristics later.
        text = re.sub(r'\[(.*?)\]', ' ', text)
        text = re.sub(r'\((.*?)\)', ' ', text)
        text = re.sub(r'\{(.*?)\}', ' ', text)
        text = re.sub(r'\$(.*?)\$', ' ', text)
        
        fixed_boundary = punctuation_model.restore_punctuation(text)        
        
        if (fixed_boundary.count(".") <= 1) or text[0].islower():
            return None

        # Strip punctuation before splitting by word: faster than a tokenizer for this purpose.
        preprocessed_text = TextCleaner.remove_punct(text)
        
        text_split = preprocessed_text.split()
        first_boundary = fixed_boundary.split(".")[0].split()[-1]
        
        # Silence failure: sketchy but avoids crashes on stray ASCII characters.
        try:
            idx = text_split.index(first_boundary)
        except Exception:
            return None
        
        # Looking to the right for a bettee boundary.
        # A boundary is assumed when an uppercase word is followed by either a lowercase word or a non-word character.
        # This is a potential failure point, but not critical... and safer than treating all non-word characters
        # as boundaries, which proved too ambiguous in practice.
        best_boundary = idx
        while idx < len(text_split) - 3:
            
            next_word = text_split[idx+1]
            next_next_word = text_split[idx+2]
            
            next_word_is_title = next_word[0].isupper()
            sentence_continuation_after = (next_next_word[0].islower() and next_next_word.isalpha())
            
            if next_word_is_title and sentence_continuation_after:
                best_boundary = idx
                break
            
            idx += 1

        return text_split[best_boundary] 

    @staticmethod
    def first_word_in(text: str, words: dict[str]) -> bool:
        text = TextCleaner.remove_punct(text)
        first_word = text.strip().split()[0].lower()
        return first_word in words
    
    @staticmethod
    def no_word_in(text: str, words) -> bool:
        words = set(text.strip().lower().split())
        return len(words)
    
    @staticmethod
    def fix_missing_boundary(text: str) -> str:
        """
        Works as a funnel to narrow down candidate header boundaries.

        First, PySegmenter splits the text into sentences (handles abbreviations, etc.).
        Running ML on full paragraphs would be too costly, so heuristics trim candidates first:

        1. Lowercase start → not a header.
        2. First word is a pronoun, connective, subordinator, or structural term (table, algorithm, etc.) → not a header.
        3. First sentence is short (≤9 words) with no pronouns, connectives, or subordinators
        → likely already a well-punctuated boundary, skip it.

        These three filters eliminate ~90% of cases before boundary detection runs.
        """
        
        # can't be a header
        if text and text[0].islower():
            return text
        
        # Pysegmter should handle abbreviations
        segments = TextFixer.split_sentences(text)
        left = segments[0]
        
        # Left is clearly a sentence
        if TextFixer.first_word_in(left, SENTENCE_MARKERS | STRUCTURE):
            return text
        
        # if small left side & multiple sentence marker => we assume it is a sentence.
        if len(left.split(" ")) <= 10 and TextFixer.no_word_in(left, SENTENCE_MARKERS | STRUCTURE) >= 3:
            return text
        
        # Restoring boundary w/ machine learning AND heuristics.
        candidate_boundary = TextFixer.find_candidate_period(left)
        
        if candidate_boundary:
            # Colon as boundary is likely to be already well-formed.
            if text.startswith(candidate_boundary + ':'):
                return text
            
            return re.sub(rf'\b{candidate_boundary}\b', candidate_boundary + '.', text, count=1)
    
        return text
    
    
    @staticmethod
    def fix_hyphen(text):
        """
        Fixes inconsistent hyphenation.
        Not critical, but reduces token count for downstream AI processing.
        """
        
        tool.enabled_rules_only = True
        tool.enabled_rules = set(["EN_SPLIT_WORDS_HYPHEN"])
        text = tool.correct(text)

        return text 
    
    @staticmethod
    def fix_lowercase_broken_boudaries(text):
        """
        Fixes merged words (e.g. "thecat was eatingbread").

        Uses MORFOLOGIK_RULE_EN_US from LanguageTool, which tends to produce false positives.
        To minimize impact, only strictly lowercase (+ hyphen) words are considered as candidates,
        and replacements are only applied if the suggestion is also strictly lowercase.
        In practice this yields clean enough results.
        """
                
        filtered_html = re.sub(r'\$(.*?)\$', ' ', text)
        filtered_html = " ".join(re.findall(r'\b[a-z][a-z-\']*\b', filtered_html))
        
        tool.enabled_rules_only = True
        tool.enabled_rules = set(["MORFOLOGIK_RULE_EN_US"])
        
        matches = tool.check(filtered_html)
        latex_formulas = re.findall(r'\$(.*?)\$', text)
        for match in matches:
            original_text = filtered_html[match.offset : match.offset + match.error_length]
            top_fix = match.replacements[0] if match.replacements else None
            
            if top_fix and len(top_fix) !=  match.error_length and not top_fix in latex_formulas:
                text = re.sub(rf'\b{match}\b', rf'\b{top_fix}\b', text)
        
        return text
