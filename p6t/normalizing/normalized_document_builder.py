import re

import pytesseract
from docling_core.types.doc import DoclingDocument

from p6t.model.dto.ir_nodes import IRCode, IRFigure, IRFootnote, IRFormula, IRHeader, IRListItem, IRSection, IRTable, \
    IRParagraph
from p6t.model.dto.ir_tree import IRTree
from p6t.model.normalized_document import NormalizedDocument
from p6t.model.parsed_document import ParsedDocument
from p6t.model.source_document import SourceDocument
from p6t.normalizing.media_resolver import MediaResolver
from p6t.normalizing.text_cleaner import TextCleaner
from p6t.normalizing.text_fixer import TextFixer


def is_abtract(heading: str) -> bool:
    return "abstract" in heading.lower()

def is_biblio(heading: str) -> bool: 
    return "references" in heading.lower() or "bibliography" in heading.lower()
    
def is_reference():
    pass

class NormalizedDocumentBuilder:
    
    def __init__(self, parsed_document: ParsedDocument):   
        self.source_document: SourceDocument = parsed_document.source_document
        self.docling_document: DoclingDocument = parsed_document.docling_document
    

    def _extract_references(self):
        ref_heading_found = False
        references = []
        prev_page = None

        for element, _ in self.docling_document.iterate_items():
            if element.label != "section_header" and not ref_heading_found:
                continue
            if element.label == "section_header" and is_biblio(element.text):
                ref_heading_found = True
                continue
            if ref_heading_found and element.label == 'section_header':
                break
            if ref_heading_found and element.label in ['text', 'list_item']:
                text = self.clean_text(element.orig)
                page = element.prov[0].page_no

                is_continuation = (
                    references
                    and text
                    and text[0].islower()
                    and page != prev_page
                )

                if is_continuation:
                    references[-1] = references[-1] + " " + text
                else:
                    references.append(text)

                prev_page = page

        return references
            
    def _collect_sections(self) -> list[list]:
        filtered = [e for e, _ in self.docling_document.iterate_items() if e.label in ['text', 'formula', 'section_header', 'list_item', 'code']]
                
        # Looking for abtract to start collection
        start_idx = next(
            (i for i, s in enumerate(filtered) if is_abtract(s.text)),
            0
        )
        
        sections = []
        curr_section = []
        for element in filtered[start_idx:]:   
            if element.label == "section_header":
                if curr_section:
                    sections.append(curr_section)

                curr_section = [element]
                    
            else:
                curr_section.append(element)
        
        if curr_section:
            sections.append(curr_section)
        
        # Building nodes
        section_nodes = []
        for e in sections:
            # By default, the starting element should be a header
            # Followed by content such as paragraph.

            # If header can't be extracted, try extracting header
            if e[0].label == 'section_header':
                starting_element = 1
                section_node: IRSection = IRSection.build(e[0])
            else:
                print(e[0].text)
                heading, text = TextFixer.extract_heading(e[0].text)
                
                # If a heading is extracted
                # We mutate the element content to only keep the paragraph
                if heading:
                    section_node: IRSection = IRSection(heading)
                else: 
                    section_node = IRSection("[SECTION]")
                
                # Paragraph was a header
                if text:
                    starting_element = 0
                    e[0].text = text
                else:
                    starting_element = 1
            
            # Build IRNodes
            for children in e[starting_element:]:
                if children.label == 'text':
                    node = IRParagraph.build(children)
                elif children.label == 'formula':
                    node = IRFormula.build(children)
                elif children.label == 'section_header':
                    node = IRHeader.build(children)
                elif children.label == 'list_item':
                    node = IRListItem.build(children)
                elif children.label == "code":
                    node = IRCode.build(children)
                
                section_node.items.append(node)
            
            section_nodes.append(section_node)
    
        # Discarding reference section & empty sections
        filtered_sections = [s for s in section_nodes if not is_biblio(s.text) and not len(s.items) == 0 ]

        return filtered_sections

    
    # PACKING & DISCARDING
    
    def _fix_headings(self, elements):
        fixed = []
        
        for element in elements:
            if isinstance(element, IRParagraph):
                heading_output = TextFixer.extract_heading(element.text)
                
                heading, paragraph = heading_output
                
                if heading:
                    self.log(f'New section heading discovered: {heading}', 3)
                    fixed.append(IRHeader(heading))
                if paragraph:
                    fixed.append(IRParagraph(paragraph))
                    
            else:
                fixed.append(element)
                
        return fixed
    
    def _discard_fake_headers(self, elements):
        """
        Some headers might be sandwiched between non-textual elements & are likely to be OCR artifacts.
        """
        cleaned = []
        i = 0
        while i < len(elements):
            current = elements[i]

            # check for sandwich: text → section_header → text
            if (
                i > 0
                and i + 1 < len(elements)
                and isinstance(elements[i-1], IRParagraph|IRListItem)
                and isinstance(current, IRHeader)
                and isinstance(elements[i+1], IRParagraph|IRListItem)
                and not elements[i-1].text.rstrip().endswith((".","!","?"))
            ):
                # fake header detected: skip it 
                i += 1
                continue

            cleaned.append(current)
            i += 1

        return cleaned
    
    def _group_forward_code_blocks(self, elements):
        """
        Hardcoded heuristics to restore text continuity around identifiable structures.
        Currently, handles: Paragraph → [Floating 'Algorithm' + 'Code'] → Paragraph.
        Should be extended as new patterns are encountered.
        """
            
        i = 0
        while i < len(elements):
            if (
                i + 3 < len(elements)
                and isinstance(elements[i], IRParagraph)
                and isinstance(elements[i+1], IRParagraph)
                and isinstance(elements[i+2], IRCode)
                and isinstance(elements[i+3], IRParagraph)
            ):  

                real_p_first = elements[i].text
                callout_p = elements[i+1].text
                # code_p = elements[i+2]
                real_p_next = elements[i+3].text
                
                
                if (real_p_first.rstrip()[-1] not in ".!?" 
                    and real_p_next[0].islower() or real_p_next[0] in ('(', ')', ',', '[', ']')
                    and callout_p.startswith(("Algorithm", "Code"))
                ):
                    elements[i].text = real_p_first + " " + real_p_next
                    elements[i+3].to_delete = True
   
            i += 1

        return [element for element in elements if not hasattr(element, 'to_delete')]
    
    def _group_forward_formula(self, elements):
        """
        Hardcoded heuristics to restore text continuity around identifiable structures.
        Currently, handles: Paragraph → [Floating 'Algorithm' + 'Code'] → Paragraph.
        Should be extended as new patterns are encountered.
        """
            
        i = 0
        while i < len(elements):
            if (
                i + 2 < len(elements)
                and isinstance(elements[i], IRParagraph)
                and isinstance(elements[i+1], IRFormula)
                and isinstance(elements[i+2], IRParagraph)
            ):  

                real_p_first = elements[i].text
                formula_el = elements[i+1].text
                real_p_next = elements[i+2].text
                
                
                if (real_p_first.rstrip()[-1] not in ".!?" 
                    and real_p_next[0].islower() or real_p_next[0] in ('(', ')', ',', '[', ']')
                ):
                    elements[i].text = real_p_first + " " + real_p_next
                    elements[i+2].to_delete = True
   
            i += 1

        return [element for element in elements if not hasattr(element, 'to_delete')]
    
    
    
    
    def _discard_unknown_text(self, elements):
        """
        Discard elements containing no recognized words.

        These likely originate from figures captured as text by OCR.
        OCR discards are rare enough that this is preferable to degrading readability.
        """
        
        
        cleaned = []
        i = 0
        while i < len(elements):
            current = elements[i]
            # checking for paragraph with no known english word.
            if (
                isinstance(current, IRParagraph) and not TextFixer.has_known_word(current.text)
            ):
                # no known word at all => discard.
                i += 1
                continue

            cleaned.append(current)
            i += 1

        return cleaned

    def _group_paragraphs_backwards(self, elements, short_prev_threshold=4):
        """
        Merge paragraph nodes backwards with two heuristics:
        1. Lowercase continuation heuristic.
        2. Merge if previous paragraph is very short (less than `short_prev_threshold` words)
        and doesn't end with punctuation.
        """
        
        grouped = elements[:]
        i = len(grouped) - 1

        while i > 0:
            curr = grouped[i]
            prev = grouped[i-1]

            if isinstance(curr, IRParagraph) and isinstance(prev, IRParagraph):
                prev_word_count = len(prev.text.split()) if prev.text else 0
                prev_ends_with_punct = prev.text.rstrip()[-1] in ".!?" if prev.text else False
                
                first_char = curr.text.strip()[0] if curr.text else None
                last_char = prev.text.rstrip()[-1] if prev.text else None
                
                # Fixing hyphenated continuations
                if last_char and last_char == "-":
                    self.log('Hyphenation continuation found', 1)
                    prev.text = prev.text.rstrip().rstrip('-')
                    prev.text += curr.text.lstrip()
                    
                    grouped.pop(i)
                    i -= 1
                    continue
                
                # Paragraph is a lowercase continuation
                lowercase_continuation = first_char and first_char.islower() and first_char.isalpha() and not prev_ends_with_punct
                
                # If random small paragraph followed by a line break.
                short_prev = prev_word_count < short_prev_threshold and not prev_ends_with_punct
                
                # ie: ref after split.
                structure_split = first_char in ['(', ')', '[', ']'] and not prev_ends_with_punct
                
                if lowercase_continuation or short_prev or structure_split:
                    self.log('Lower case continuation found', 1)
                    prev.text += " " + curr.text
                    grouped.pop(i)
                    i -= 1
                    continue
                            
            i -= 1

        return grouped
    
    def best_rotation(self, img):
        # image_to_osd returns a dictionary containing orientation info
        try:
            osd = pytesseract.image_to_osd(img, output_type=pytesseract.Output.DICT)
        except Exception:
            self.log('Tesseract fail. Defaulting to base angle', 2)
            return img
        
        return img.rotate(-osd['rotate'], expand=True)
    
    def log(self, log, level=None):
        print(f'{' ' * level if level else ''}{log}')

    def run_and_log_transformation(self, fn_input, fn, log='', level=0):
        fixed = fn(fn_input)
        
        if log and fixed != fn_input:
            self.log(log, level)

        return fixed 
    
    def clean_text(self, text):
        # Normalize Unicode Chars
        text = TextCleaner.unify_unicor_chars(text)
        
        # Line break hyphenation
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
        
        # Unifying spacing
        text = TextCleaner.unify_spacing(text)
        
        # Removing unnecessary LaTex formatting
        text = TextCleaner.remove_latex_formatting(text)
        
        # Converting to ascii and using $ instead of math tags.
        text = TextCleaner.normalize_inlined_maths(text)

        # Footnote normalization
        text = TextCleaner.textify_footnotes(text)
        
        # Collapsing texts refs into predictable words
        text = TextCleaner.normalize_structure_in_text(text)

        # Removing HTML tags
        text = TextCleaner.remove_html_tags(text)

        # Fixing backed refs.
        text = TextCleaner.fix_and_collapse_bracket_ref(text)
    
        # Fixing broken words
        text = TextFixer.fix_lowercase_broken_boudaries(text)
        
        # Removing leading bullet marker
        text = TextCleaner.clean_bullet_text(text)
        
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text.strip()

    def clean_footnote(self, orig, surya):
        # Reject Surya parse.
        if not re.findall(r"<math>(.*?)</math>", surya, re.DOTALL):
            return self.clean_text(orig)
        else:
            surya = re.sub(r'<sup>\^?(.*?)</sup>', r'\1 ', surya)
            surya = re.sub(r'<math>\^(\d+)</math>', r'\1 ', surya)
            return self.clean_text(surya)

    def clean_formula(self, text):
        text = TextCleaner.remove_html_tags(text)
        text = TextCleaner.remove_latex_formatting(text)
        text = TextCleaner.normalize_latex(text)
        text = TextCleaner.format_latex_alignment(text)
        
        # This is seeming to be related to CodeFormulaV2
        text = text.rstrip('\\..')
        text = text.rstrip('\\,,')
        text = text.rstrip('\\,.')
        text = text.rstrip('\\.,')
        
        return text


    def build(self) -> NormalizedDocument:    
        
        # Proprocessing the parse
        # - Discarding headers / footers categorized as code
        # - Picking best source between OCR / backend-text
        # - Repairing brackets if necessary
        # TODO : Align sentence per sentence!
        self.log('Preprocessing Parse output', 0)
        for e, _ in self.docling_document.iterate_items():            
            
            # It seems some headers/footers may get categorized as code.
            if e.label == "code" and len(e.orig) < 10:
                e.label = "_DISCARD_"

            # Picking backend text if possible, else repairing OCR output.
            if e.label in ["text", "list_item", "footnote", "caption"]:
                if r"<\sup>" in e.text or r"</math>" in e.text:
                    # Removing line breaks 
                    text = e.text
                    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
                    text = re.sub('\n+', ' ', text)
                    
                    # Adding brackets where missed
                    e.text = TextCleaner.fix_ocr_brackets(text, e.orig)
                else:
                    e.text = e.orig

        
        # During cleaning:
        # - Spaces are normalized around punctuation.
        # - Unicode characters are collapsed to ASCII equivalents.
        # - Known structural elements (tables, figures, etc.) are collapsed to a single identifier (e.g. "sec." -> "section").
        # - LaTeX formatting commands from Surya are stripped. If inline math is missing content, leftover formatting is the likely culprit.
        # - Footnote structure is uniformized
        # - Broken OCR wording is repaired
        # - Broken OCR boundaries (missing punct) are repaired.
        # - After this step, tthere should be no remaining tags or odd latex formatting.
        self.log('Applying text normalization to elements', 0)       
        for e, _ in self.docling_document.iterate_items():
            if e.label == 'text':
                self.log(f'Normalizing {e.self_ref}' , 1)
                e.text = self.clean_text(e.text)
                
            elif e.label == 'list_item':
                self.log(f'Normalizing {e.self_ref}' , 1)
                e.text = self.clean_text(e.text)
                no_words = len(e.text.split())
                if no_words >= 80:
                    e.label == 'text'
            elif e.label == 'formula':
                self.log(f'Normalizing {e.self_ref}' , 1)
                e.text = e.text if e.text else e.orig
                e.text = self.clean_formula(e.text)
            elif e.label == 'footnote':
                self.log(f'Normalizing {e.self_ref}' , 1)
                e.text = self.clean_footnote(e.orig, e.text)
            elif e.label == 'code':
                e.text = TextCleaner.remove_latex_formatting(e.text)
            elif e.label == 'caption':
                e.text = self.clean_text(e.text)
            
        self.log('Discarding OCR soup', 0)  
        for e, _ in self.docling_document.iterate_items():
        # No english words
        # If not an empty space, this may indicate Docling missed parts of structures such as Tables or Figures
        # Future versions should investigate __DISCARD__ labels 
            if e.label in ['text','list_item']:
                if not TextFixer.has_known_word(e.text):
                    self.log(f'Discarding {e.self_ref}' , 1)
                    e.label = "__DISCARD__"

        self.log('Extracting title', 0)
        paper_title =[e.text for e,_ in list(self.docling_document.iterate_items()) if e.label == 'section_header'][0]
        
        self.log('Extracting references', 0) 
        document_references = self._extract_references()
        
        # --- Media Collection ---
        # Elements are re-cropped from source for quality.
        #
        # 1. Resolve known elements: match tables and pictures to their captions.
        # 2. Resolve unknowns:
        #    - discard duplicates (tables often have a redundant figure version)
        #    - discard obvious artifacts (e.g. stray decorative elements)
        # 3. Group adjacent pictures assumed to form a single visual split by the parser.
        # 4. Treat code blocks followed by a caption as figures.
        self.log('Resolving Medias', 0) 
        medias = MediaResolver(self.docling_document, self.source_document).run()
        
        # Tables are sometimes captured as pictures, so the caption is used as the source of truth.
        # Rotation is not guaranteed, so Tesseract is used to correct the angle beforehand.
        # Captions are typically in caption_text(), but .text was populated upstream for convenience.
        self.log('Mapping medias to their caption', 0) 
        tables, figures = [], []
        for img, caption in medias:
            final_img = self.run_and_log_transformation(img, self.best_rotation, 'Fixed media rotation', level=1)
            
            if re.search(r'\b(table)\b', caption.lower()):
                tables.append(IRTable.build(caption, final_img))
            else:
                figures.append(IRFigure.build(caption, final_img))
        
        # Collecting Footnotes
        self.log('Collecting footnotes', 0) 
        footnotes = [IRFootnote.build(e) for e, _ in self.docling_document.iterate_items() if e.label == 'footnote']
        
        # Grouping sections together
        # Discarding everything before abtract (either in text or as a header)
        # Discarding reference sections
        # Some important considerations
        # - Only "section_header" count as header during this phase
        # - This assumption helps to figure levels downstream capture section header are likely to be main heading elements
        self.log('Collecting sections', 0) 
        sections = self._collect_sections()

        # This improves readability, though the approach is admittedly hacky.
        # Most OCR artifacts seem to originate from bad crops during the Docling parse.
        # These are rare enough that other heuristics usually catch them before this point.
        # This yields the need for further work to infer structure from these artifacts.
        self.log('Discarding fake headers', 1) 
        for section in sections:
            # Sandwiched heading (most likely part of a figure group that was re-OCRed)
            section.items = self._discard_fake_headers(section.items)

        # Repairs sentence boundaries using a mix of deep learning and heuristics.
        #
        # Writers often compress space for publication by using bold text instead of proper headers.
        # A parser can't infer that, and it reads something like: "Fixing continuity We show that..."
        # Similarly, words may be merged (thecat) or missing hyphens across line breaks.
        #
        # Headers are extracted in a later pass; at this stage we just want semantically cohesive text.
        # Extracts headers from reconstructed boundaries.
        self.log('Repairing sentence boundaries', 0)
        for section in sections:
            for item in section.items:
                if isinstance(item, IRParagraph):
                    item.text = TextFixer.fix_missing_boundary(item.text)

        # Docling is great at inferring structure, but outputs elements linearly.
        # We use heuristics to infer reading order and how paragraphs should be grouped.
        #
        # Backward grouping works upstream from the current element.
        # Forward grouping resolves logical units that span multiple structural elements
        #   (e.g. a floating theorem + code block + paragraph treated as one unit).
        # Only this case is handled for now. this function should be extended as more structures are encountered.
        #
        # Hardcoding is unavoidable here.
        self.log('Fixing text continuity', 1)
        for section in sections:
            # Working backward
            section.items = self._group_paragraphs_backwards(section.items)
            # Working forward, skipping as soon as pattern can't be found
            section.items = self._group_forward_code_blocks(section.items)
            section.items = self._group_forward_formula(section.items)
            
        # Extracts headers from reconstructed boundaries.
        # While heuristics are good at detecting clear sentences, they may misclassify edge case.
        # Special cases should be added to TextUnifier.is_heading
        self.log('Resolving missing headings', 1) 
        for section in sections:
            section.items = self._fix_headings(section.items)

        self.log('Fixing hyphenation', 1) 
        for section in sections:
            for item in section.items:
                # Fixing hyphenation
                if isinstance(item, IRParagraph):
                    item.text = TextFixer.fix_hyphen(item.text)
        # Reconstruct hierarchy from numbering. 
        # first header is top level, subsequent ones are parent + 1.
        self.log('Resolving section level', 1) 
        tree = IRTree.build(sections)
        
        return NormalizedDocument(
            paper_title,
            tree, 
            footnotes, 
            tables, 
            figures,
            document_references
        )