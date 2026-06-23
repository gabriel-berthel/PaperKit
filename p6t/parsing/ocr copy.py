from typing import List
from surya.foundation import FoundationPredictor
from surya.recognition import DetectionPredictor, RecognitionPredictor
from surya.common.surya.schema import TaskNames
from typing import List
from PIL.Image import Image as PILImage

class SuryaLatexOCR():
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            foundation = FoundationPredictor()
            cls._instance.predictor = RecognitionPredictor(foundation)
        return cls._instance

    def run_blocks(self, images):
        
        foundation_predictor = FoundationPredictor()
        det_predictor = DetectionPredictor()
        rec_predictor = RecognitionPredictor(foundation_predictor)

        # ocr_without_boxes
        predictions = rec_predictor(
            images,
            task_names=[TaskNames.ocr_without_boxes] * len(images),
            det_predictor=det_predictor,
            math_mode=True,
        )


        return [
            "\n".join(line.text for line in p.text_lines) if p.text_lines else ""
            for p in predictions
        ]