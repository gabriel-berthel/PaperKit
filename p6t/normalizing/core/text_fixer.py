
import re
import pysbd
from deepmultilingualpunctuation import PunctuationModel  
import language_tool_python
from nltk.corpus import words

from p6t.normalizing.core.text_cleaner import TextCleaner

tool = language_tool_python.LanguageTool('en-US')
seg = pysbd.Segmenter(language="en", clean=False, doc_type=None)
word_set = set(words.words())
punctuation_model = PunctuationModel()

PRONOUNS = {
    'i', 'we', 'they', 'he', 'she', 'it',
    'our', 'their', 'his', 'her', 'its', 'my',
    'this', 'these', 'those', 'the',
}

CONNECTIVES = {
    # Addition
    'moreover', 'furthermore', 'additionally', 'also', 'besides',
    # Contrast
    'however', 'nevertheless', 'nonetheless', 'yet', 'although', 'though',
    # Cause/result
    'therefore', 'thus', 'hence', 'consequently', 'accordingly',
    # Sequence
    'finally', 'subsequently', 'meanwhile', 'previously',
    # Illustration
    'specifically', 'notably', 'particularly', 'importantly', "by", "in", "to", "despite"
}

STRUCTURE = {
    "table", "figure", "section", "theorem", "definition", "lema", "algorithm"
}

SUBORDINATORS = {
    # Time
    'when', 'while', 'after', 'before', 'since', 'until', 'once',
    # Condition
    'if', 'unless', 'whether', 'provided',
    # Cause
    'because', 'since', 'as',
    # Contrast
    'although', 'though', 'whereas', 'while',
    # Other
    'that', 'which', 'where', 'who', 'whom',
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
        
        # not looking up non alpha words (tho set operations are already fast)
        for w in text.split():
            w = w.lower()
            if len(w) > 2 and w.isalpha() and w in word_set:
                return True
            
            
        return False

    @staticmethod
    def is_heading(sentence):
        """
        Assumes sentence boundaries have been fixed upstream.
        If headers are being misclassified, the heuristics here are the likely culprit.
        """
        
        # Missed paragraph continuation
        if sentence[0].islower() or not sentence[0].isalnum():
            return False
            
        # Known non-header patterns. Regex would catch more but risks introducing
        # more bugs than it solves — these cases are rare enough that explicit checks are safer.
        if "et al" in sentence or "keywords:" in sentence.lower():
            return False
        
          # No recognized words → likely an artifact, table fragment, or missed formula.
        # Better to leave it as a paragraph than misclassify it.
        header_words = TextCleaner.remove_punct(sentence)
        if not TextFixer.has_known_word(header_words):
            return False

        # Short sentence with no pronouns, connectives, or subordinators → likely a header.
        if len(header_words.split()) <= 10 and not TextFixer.first_word_in(sentence, PRONOUNS | CONNECTIVES | STRUCTURE | SUBORDINATORS):
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
            return left, " ".join(sentences[1:]).strip()
        
        return None, text
    
    @staticmethod
    def remove_punct(text):
        return re.sub(r"(?<!\d)[.,;:!?'](?!\d)","",text) 
   
    @staticmethod
    def find_first_missing_punct(text):
        """
        Deepmultilingualpunctuation is slow but produces good results for punctuation restoration.
        It can't infer headers though, so we locate an initial boundary, then scan adjacent words
        for a better split: headings tend to capitalize most words, which serves as the signal.
        """
                
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
    def any_word_in(text: str, words) -> bool:
        words = set(text.strip().lower().split())
        return bool(words & (words))
    
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
        if text[0].islower():
            return text
        
        # Pysegmter should handle abbreviations
        segments = TextFixer.split_sentences(text)
        left = segments[0]
        
        # rejected, most likely a no normal sentence.
        if TextFixer.first_word_in(left, PRONOUNS | CONNECTIVES | STRUCTURE | SUBORDINATORS):
            return text
        
        # rejected, because boundary is very likely to be already good.
        if len(left.split(" ")) <= 9 and not TextFixer.any_word_in(left, PRONOUNS | CONNECTIVES | SUBORDINATORS):
            return text
        
        # Restoring boundary w/ machine learning AND heuristics.
        missing_boundary = TextFixer.find_first_missing_punct(left)
        
        if missing_boundary:
            return re.sub(rf'\b{missing_boundary}\b', missing_boundary + '.', text, count=1)
    
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
                
        filtered_html = re.sub(r'$(.*?)$', ' ', text)
        filtered_html = " ".join(re.findall(r'\b[a-z][a-z-\']*\b', filtered_html))
        
        tool.enabled_rules_only = True
        tool.enabled_rules = set(["MORFOLOGIK_RULE_EN_US"])
        
        matches = tool.check(filtered_html)
        for match in matches:
            original_text = filtered_html[match.offset : match.offset + match.error_length]
            top_fix = match.replacements[0] if match.replacements else None
            
            if top_fix and top_fix.islower():
                text = text.replace(original_text, top_fix)
        
        return text

        """
        Strips formatting commands from LaTex.
        Not removing them degrades LaTex handling dowstreams.
        """
        
        # Font style commands (mathbf, mathtt, textbf, etc.)
        for cmd in [
            r'\\mathbf', r'\\mathtt', r'\\mathit', r'\\mathsf', r'\\mathbb', r'\\mathcal',
            r'\\mathfrak', r'\\mathscr', r'\\mathrm', r'\\mathds',
            r'\\textbf', r'\\texttt', r'\\textit', r'\\textrm', r'\\textsf',
            r'\\textsc', r'\\textsl', r'\\emph', r'\\text',
            r'\\boldsymbol', r'\\bm',
        ]:
            text = re.sub(cmd + r'\{([^}]*)\}', r'\1', text)

        # Size commands with braces
        for cmd in [
            r'\\tiny', r'\\scriptsize', r'\\footnotesize', r'\\small',
            r'\\normalsize', r'\\large', r'\\Large', r'\\LARGE',
            r'\\huge', r'\\Huge',
        ]:
            text = re.sub(cmd + r'\{([^}]*)\}', r'\1', text)

        # Color and box commands
        for cmd in [r'\\textcolor\{[^}]*\}', r'\\colorbox\{[^}]*\}', r'\\fcolorbox\{[^}]*\}\{[^}]*\}']:
            text = re.sub(cmd + r'\{([^}]*)\}', r'\1', text)
            text = text.replace(r'\mathcal{E}', '&')
            
        return text