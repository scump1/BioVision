
import os

from controller.algorithms.bubble_sizer.steps.preprocessor import Preprocessor
from controller.algorithms.bubble_sizer.steps.processor import ImageProcessor
from controller.algorithms.bubble_sizer.steps.postprocessor import PostProcessor

class BubbleSizeAnalyzer:

    def __init__(self, calibpath = None) -> None:

        self.calibpath = calibpath

    def process_image(self, path, visibility: bool = False) -> dict:

        try:
            
            # Preprocess the image
            preprocessor = Preprocessor(path, self.calibpath)
            self.preprocessed_image = preprocessor.preprocess()

            if visibility:
                # process with visibility
                imageprocessor = ImageProcessor(self.preprocessed_image, path, True)
                result, metadata, image = imageprocessor.img_process()
            else:
                # Process the image
                imageprocessor = ImageProcessor(self.preprocessed_image, path)
                result, metadata = imageprocessor.img_process()

            # Extract results and values
            # this turns the ellipsoidal results (if there) into circle results and generates additional information
            postprocessor = PostProcessor(result)
            data = postprocessor.process()

            name = os.path.basename(path)

            if visibility:
                return {
                    "Image": name,
                    "Data": data,
                    "Metadata": metadata
                }, image
            else:
                return {
                    "Image": name,
                    "Data": data,
                    "Metadata": metadata
                }

        except Exception as e:
            print(e)