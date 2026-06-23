
import re
import unicodedata
from pylatexenc.latex2text import LatexNodes2Text

texer = LatexNodes2Text()

class TextCleaner:
    
    @staticmethod
    def match_case(replacement: str, original: str) -> str:
        if original.isupper():
            return replacement.upper()
        if original[0].isupper():
            return replacement.capitalize()
        return replacement.lower()

    @staticmethod
    def normalize_structure_in_text(text: str):
        patterns = [
            (r"\b(table|tables|tab\.?|tabs\.?|tbl\.?|tbls\.?)\b", "table"),
            (r"\b(figure|figures|fig\.?|figs\.?)\b", "figure"),
            (r"\b(section|sec\.?|sect\.?|chapter|ch\.?|§+)\b", "section"),
            (r"\b(equation|equations|eq\.?|eqs\.?|eqn\.?)\b", "equation"),
            (r"\b(appendix|appendices|app\.?|append\.?)\b", "appendix"),
            (r"\b(algorithm|alg\.?|algs\.?)\b", "algorithm"),
            (r"\b(references|reference|ref\.?|refs\.?|bibliography|works cited)\b", "references"),
            (r"\b(footnote|fn\.?)\b", "footnote"),
            (r"\b(page|p\.?|pp\.?)\b", "page"),
        ]
        
        cleanup_patterns = [
            r"\b(table|figure|section|equation|appendix|algorithm|references|footnote|page)\.",
        ]


        for pattern, replacement in patterns:
            def repl(match):
                return TextCleaner.match_case(replacement, match.group(0))
            
            text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
        
        for pattern in cleanup_patterns:
            text = re.sub(pattern, r"\1", text, flags=re.IGNORECASE)
        
        text = re.sub(r'§', r'section ', text)
        
        return text
    
    @staticmethod
    def fix_and_collapse_bracket_ref(text: str) -> str:
        """
        Collapses sequences like [1][2][3] into [1, 2, 3].
        """

        # Repair bracket ref ahead
        text = re.sub(r'\[(\d+)\s', r'[\1]', text)
    
        pattern = re.compile(r'(?:\[(\d+)\]\s?){2,}')

        def repl(match):
            nums = re.findall(r'\[(\d+)\]', match.group(0))
            return f"[{', '.join(nums)}]"

        return pattern.sub(repl, text)

    @staticmethod
    def textify_footnotes(text):
        return  re.sub(r"<sup>(.*?)</sup>", r"footnote \1", text)
    
    @staticmethod
    def crush_latex_spaces(latex):
        protected = []

        def save(m):
            protected.append(m.group(0))
            return f"@@{len(protected)-1}@@"

        # protect commands with one {...} argument
        
        latex = re.sub(r'\\[a-zA-Z]+\{[^{}]*\}', save, latex)
        latex = re.sub(r'\\[a-zA-Z]+', save, latex)
        latex = re.sub(r' ([A-Za-z])+ ', '\1', latex)
        latex = re.sub(r'>', ' > ', latex)
        latex = re.sub(r'<', ' < ', latex)

        for i, value in enumerate(protected):
            latex = latex.replace(f"@@{i}@@", f' {value} ')
            
        return latex.strip()
    
    @staticmethod
    def normalize_inlined_maths(text):
        def repl(match):
            latex = match.group(1)
            
            if (latex.strip() == texer.latex_to_text(latex).strip()) \
            and not re.match(r'[A-Za-z]+\([^\)]\)', latex) or re.match(r'[A-Za-z]+\[[^\]]\]', latex) :
                return latex
            
            return f" $ {TextCleaner.crush_latex_spaces(latex)} $ "
            
        return re.sub(r"<math(?: [^>]+)?>(.*?)</math>", repl, text, flags=re.DOTALL)
    
    @staticmethod
    def unify_unicor_chars(text: str) -> str:
        text = unicodedata.normalize("NFC", text)
        
        # Zero-width / invisible chars
        text = re.sub(r"[\u200B-\u200D\uFEFF\u2060]", "", text)

        # Normalize whitespace variants
        text = (text
        .replace("\xa0", " ")   # non-breaking space
        .replace("\u2000", " ")
        .replace("\u2001", " ")
        .replace("\u2002", " ")
        .replace("\u2003", " ")
        .replace("\u2004", " ")
        .replace("\u2005", " ")
        .replace("\u2006", " ")
        .replace("\u2007", " ")
        .replace("\u2008", " ")
        .replace("\u2009", " ")
        .replace("\u200A", " ")
        .replace("\u202F", " ")
        .replace("\u205F", " ")
        .replace("\u3000", " ")
        )
            
        # Normalize dashes / hyphens
        text = re.sub(r"[‐-‒–—―−]", "-", text)

        # Normalize quotes
        text = re.sub(r"[‘’‚‛‹›`]", "'", text)
        text = re.sub(r'[“”„‟«»]', '"', text)

        # Normalize ellipsis
        text = text.replace("…", "...")

        # Normalize bullets
        text = re.sub(r"[•◦▪▸▹►▻]", "-", text)

        # Normalize slashes
        text = re.sub(r"[⁄∕]", "/", text)

        # Normalize line endings
        text = re.sub(r"\r\n?", "\n", text)

        text = (
            text
            .replace("\xa0", " ")
            .replace("–", "-")
            .replace("—", "-")
        )
        
        return text
    
    @staticmethod
    def _mask_protected(text: str) -> tuple[str, dict]:
        """Mask math, numbers, and URLs before normalization."""
        placeholders = {}
        counter = 0

        def mask(pattern, flags=0):
            nonlocal counter, text
            for match in re.finditer(pattern, text, flags):
                key = f"__PROTECTED_{counter}__"
                placeholders[key] = match.group(0)
                text = text.replace(match.group(0), key, 1)
                counter += 1

        # Mask <math>...</math> blocks (including multiline)
        mask(r'<math(?: [^>]+)?>.*?</math>', re.DOTALL)

        # Mask decimals: 3.14, .5
        mask(r'\d*\.\d+')
        
        # et al. kinda abbr
        mask(r'\w\.\'')

        # Mask thousands separators: 1,000 / 1,000,000
        mask(r'\d{1,3}(?:,\d{3})+')
        
        # Mask urls
        mask(r'https?://\S+')
        
        # mask emails
        mask(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

        return text, placeholders

    @staticmethod
    def _unmask_protected(text: str, placeholders: dict) -> str:
        """Restore all masked content."""
        for key, value in placeholders.items():
            text = text.replace(key, value)
        return text

    @staticmethod
    def clean_bullet_text(s: str) -> str:
        bullet_chars = "•*-–—-·"  # add or remove chars as needed
        return s.strip().lstrip(bullet_chars)

    @staticmethod
    def unify_spacing(text: str) -> str:
        text, placeholders = TextCleaner._mask_protected(text)

        # Add space after punctuation if missing
        text = re.sub(r'([.,:;!?])(?=[^\s__])', r'\1 ', text)
        # Remove spaces before punctuation
        text = re.sub(r'\s+([,.;:!?])(?!\s*_)', r'\1', text)

        # Fix parenthesis spacing
        text = re.sub(r'\(\s+', '(', text)
        text = re.sub(r'\s+\)', ')', text)

        # Normalize newlines and collapse spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        text = TextCleaner._unmask_protected(text, placeholders)
        return text

    @staticmethod
    def remove_punct(text):
        return re.sub(r"(?<!\d)[.,;:!?'](?!\d)","",text) 
    
    @staticmethod
    def remove_html_tags(text):
        return re.sub(r"</?[^>]+>", "", text)
    
    @staticmethod
    def format_latex_alignment(text):
        if "&" in text:
            # Multi-line aligned formula 
            text = r"\begin{align}" + "\n" + text + "\n" + r"\end{align}"
            
        return text

    @staticmethod
    def remove_latex_formatting(text):
        """
        Strips formatting commands from LaTex.
        Not removing them degrades LaTex handling dowstreams.
        """
        
        # Unwrapping text from math
        text = re.sub(r'\\text\{([^}]*)\}', r'</math> \1 <math>', text)
        
        # Font style commands (mathbf, mathtt, textbf, etc
        for cmd in [
            r'\\mathbf', r'\\mathtt', r'\\mathit', r'\\mathsf', r'\\mathbb', r'\\mathcal',
            r'\\mathfrak', r'\\mathscr', r'\\mathrm', r'\\mathds',
            r'\\textbf', r'\\texttt', r'\\textit', r'\\textrm', r'\\textsf',
            r'\\textsc', r'\\textsl', r'\\emph',
            r'\\boldsymbol', r'\\bm', r'\\boxed',
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