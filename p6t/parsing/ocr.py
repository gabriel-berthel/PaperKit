from typing import List
from surya.inference import SuryaInferenceManager
from surya.recognition import RecognitionPredictor
from surya.layout import LayoutPredictor
from typing import List
from PIL.Image import Image as PILImage

class SuryaLatexOCR():
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            manager = SuryaInferenceManager() # auto-spawns vllm or llama-server
            cls._instance.predictor = RecognitionPredictor(manager)

        return cls._instance

    def run_single_block(self, images: List[PILImage]) -> List[str]:
        predictions = self.predictor(images)

        return [
            " ".join(
                block.html for block in p.blocks
                if hasattr(block, "html") and block.html
            )
            for p in predictions
        ]