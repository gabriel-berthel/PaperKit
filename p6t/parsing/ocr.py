from surya.foundation import FoundationPredictor
from surya.recognition import DetectionPredictor, RecognitionPredictor
from surya.common.surya.schema import TaskNames
from typing import List
from PIL.Image import Image as PILImage
from typing import List

from PIL.Image import Image as PILImage
from surya.common.surya.schema import TaskNames
from surya.foundation import FoundationPredictor
from surya.recognition import DetectionPredictor, RecognitionPredictor


class SuryaLatexOCR():
    
    def run_formulas(self, images: List[PILImage]) -> List[str]:
        foundation_predictor = FoundationPredictor()
        rec_predictor = RecognitionPredictor(foundation_predictor)
        
        
        tasks = [TaskNames.block_without_boxes] * len(images)
        bboxes = [[[0, 0, img.width, img.height]] for img in images]
        
        predictions = rec_predictor(
            images,
            tasks,
            bboxes=bboxes,
        )

        return [
            p.text_lines[0].text if p.text_lines else ""
            for p in predictions
        ]
        
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