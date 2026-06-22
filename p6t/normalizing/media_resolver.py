from dataclasses import dataclass
import itertools

from docling_core.types.doc import DoclingDocument
from p6t.model.source_document import SourceDocument


@dataclass
class MediaResolver:
    document: DoclingDocument
    source_document: SourceDocument

     # ----------------- utils -----------------

    def crop(self, element):
        bbox = element.prov[0].bbox
        page = element.prov[0].page_no
        return self.source_document.crop(page, bbox)

    def bbox_area(self, bbox):
        return abs(bbox.r - bbox.l) * abs(bbox.b - bbox.t)

    def is_emote(self, element):
        bbox = element.prov[0].bbox
        return self.bbox_area(bbox) <= 300
    
    def media_key(self, element):
        bbox = element.prov[0].bbox
        page = element.prov[0].page_no

        # rounding avoids float instability issues
        return (
            page,
            element.label,
            round(bbox.l, 2),
            round(bbox.t, 2),
            round(bbox.r, 2),
            round(bbox.b, 2),
        )
    

    # ----------------- bootstrap index -----------------

    def build_direct_index(self):
        """
        Mapping medias with their attached caption.
        This should resolve 95% of medias.
        """
        index = {}
        bbox_set = list()

        for media in self.document.pictures + self.document.tables:

            caption = media.caption_text(self.document)

            if not caption:
                continue

            index[caption] = (self.crop(media), caption)
            bbox_set.append(media.prov[0].bbox)

        return index, bbox_set

    # ----------------- fallback grouping -----------------

    def resolve_picture_group(self, unknown):
        """
        Resolves pictures that share a caption by grouping adjacent ones.

        When two pictures appear side by side under a single caption, a human reads
        it as one continuous zone. but the upstream parser.. it's two separate
        picture elements with no attached caption. This method groups such adjacent
        pictures so they can be resolved together.
        """

        page_no = unknown.prov[0].page_no
        elements = [e for e, _ in self.document.iterate_items(page_no=page_no)]

        idx = elements.index(unknown)

        # BEFORE: contiguous pictures only
        before = list(itertools.takewhile(
            lambda e: e.label == "picture",
            reversed(elements[:idx])
        ))
        before.reverse()

        # AFTER: pictures + caption until break
        after = list(itertools.takewhile(
            lambda e: e.label in {"picture", "caption"},
            elements[idx + 1:]
        ))

        group = before + [unknown] + after

        pictures = [e for e in group if e.label == "picture"]
        captions = [e for e in group if e.label == "caption"]

        if len(captions) != 1 or not pictures:
            return None
        
        caption = captions[0].text
        merged = self.merge_horizontal(pictures)

        return merged, caption

    # ----------------- merging -----------------

    def merge_horizontal(self, pictures):
        """
        Merging pictures horizontally. 
        """
        
        if len(pictures) == 1:
            return self.crop(pictures[0])

        a = pictures[0].prov[0].bbox
        b = pictures[-1].prov[0].bbox

        merged_bbox = type(a)(
            l=min(a.l, b.l),
            r=max(a.r, b.r),
            t=min(a.t, b.t),
            b=max(a.b, b.b),
        )

        return self.source_document.crop(pictures[0].prov[0].page_no, merged_bbox)

    # ----------------- main pipeline -----------------

    
    def run(self):
        """
        Fully autonomous pipeline:
        - discovers all media
        - resolves known ones
        - infers unknown one:
            - Groups of pictures
            - Figures parsed as "code"
        """

        resolved, known_bboxes = self.build_direct_index()
        final = []
        final.extend(resolved.values())

        # collecting all medias
        all_media = self.document.pictures + self.document.tables
        for media in all_media:
            
            # Discard small emoticons or OCR artifacts
            if self.is_emote(media):
                continue

            # Already solved. Skip!
            if media.prov[0].bbox in known_bboxes:
                continue

            # Could be multiple figure next to one another
            result = self.resolve_picture_group(media)

            if not result:
                continue

            merged, caption = result

            final.append((merged, caption))

        # resolving missed code block figures
        # Assumption being code with a caption right bellow = a figure.
        items = [e for e, _ in self.document.iterate_items()]  
        for code in items:
            if code.label != 'code':
                continue
            
            code_bbox = code.prov[0].bbox
            
            # Check if the next sibling is a caption
            current_idx = items.index(code)
            next_item = items[current_idx + 1]
            
            if next_item and next_item.label == 'caption':
                caption = next_item
                caption_bbox = caption.prov[0].bbox
                page_no = caption.prov[0].page_no
           
                a = code_bbox
                b = caption_bbox
                merged_bbox = type(a)(
                    l=min(a.l, b.l),
                    r=max(a.r, b.r),
                    t=a.t,   # top of code block (highest point)
                    b=b.t + 10,   # top of caption = bottom limit
                )
                
                crop = self.source_document.crop(page_no, merged_bbox)
                final.append((crop, caption.text))
                
                # mutating label so code block is discarded dowstream
                code.label = "__discard__"
            
        return final