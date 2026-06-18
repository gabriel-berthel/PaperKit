from pdf2image import convert_from_path
from PIL import Image
import base64
from io import BytesIO
import hashlib

class SourceDocument:
    
    @staticmethod
    def hash_doc(path):
        with open(path, "rb") as f:
            pdf_bytes = f.read()
            
        return hashlib.sha256(pdf_bytes).hexdigest()
    
    def __init__(self,path, dpi=300):
        """
        Loads a PDF and converts each page into a PIL image.

        Attributes:
            pages: dict[int, PIL.Image] - page_number -> page image
            path: original file path for provenance
        """
        
        self.path = path
        self.pages = {}  # page_number -> PIL image
        
        with open(path, "rb") as f:
            self.pdf_bytes = f.read()
            
        self.pdf_hash = hashlib.sha256(self.pdf_bytes).hexdigest()
        
        pil_pages = convert_from_path(path, dpi=dpi)
        for i, page in enumerate(pil_pages, start=1):
            self.pages[i] = page

    def get_page(self, page_number: int) -> Image.Image:
        """Return the PIL image for the given page number"""
        return self.pages.get(page_number, None)

    def save_page(self, page_number: int, file_path: str):
        """Save a specific page to disk"""
        page = self.get_page(page_number)
        if page:
            page.save(file_path, format="PNG")
        else:
            raise ValueError(f"Page {page_number} does not exist.")

    def to_base64(self, page_number: int) -> str:
        """Return base64 string of the page image for embedding in IR"""
        page = self.get_page(page_number)
        if not page:
            raise ValueError(f"Page {page_number} does not exist.")
        buffered = BytesIO()
        page.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    def pdf_bbox_to_pil(self, bbox, page_height, scale=1.0):
        """
        Convert a PDF-style bbox (l, t, r, b) to a PIL crop box.
        Returns (left, top, right, bottom)
        """
        x1 = bbox.l * scale
        x2 = bbox.r * scale

        top = page_height - (bbox.t * scale)    # smaller y in PIL coordinates
        bottom = page_height - (bbox.b * scale) # larger y in PIL coordinates
        
        if top > bottom:
            top, bottom = bottom, top
        
        return (x1, top, x2, bottom)

    def resize_max_2048(self, img) -> Image.Image:
        """
        Longest size can only be 2048px. 
        """
        max_side = 2048

        w, h = img.size
        scale = min(1.0, max_side / max(w, h))

        if scale < 1.0:
            img = img.resize(
                (int(w * scale), int(h * scale)),
                Image.BILINEAR
            )

        return img

    def crop(self, page_number: int, bbox: dict, scale: float = 300/72) -> Image.Image:
        """
        Crop a region from a page, converting PDF bbox to PIL coords.

        Args:
            page_number: page to crop
            bbox: dict with keys 'l','r','b','t' (PDF coords, bottom-left origin)
            scale: points -> pixels conversion factor

        Returns:
            PIL.Image of cropped region
        """

        page = self.get_page(page_number)
        box = self.pdf_bbox_to_pil(bbox, page.height, scale)
        padded = (box[0] - 10, box[1] - 10, box[2] + 10, box[3] + 10)
        return page.crop(padded)