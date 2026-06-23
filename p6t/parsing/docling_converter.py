from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import DoclingDocument

class DoclingConverter:
    def __init__(self):
        self._build()
        self.converter = self._build_converter()

    def _build(self):
        self.pipeline_options = PdfPipelineOptions(
            do_ocr=False,
            do_formula_enrichment=False,
            do_code_enrichment=False,
            images_scale=1.0,

        # Keep table structure enabled even though it's not used downstream.
        # It improves parsing quality by ensuring tables are fully recognized
        # and reduces reliance on brittle cropping heuristics.
            do_table_structure=True,
        )
        
    def _build_converter(self):
        return DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=self.pipeline_options
                ),
            }
        )

    def parse(self, path) -> DoclingDocument:
        print(f"OCR: {self.pipeline_options.do_ocr}")
        print(f"Formula: {self.pipeline_options.do_formula_enrichment}")
        print(f"Code: {self.pipeline_options.do_code_enrichment}")
        print(f"Tables: {self.pipeline_options.do_table_structure}")
        print("Parsing with docling (this may take some time)")
        return self.converter.convert(path).document