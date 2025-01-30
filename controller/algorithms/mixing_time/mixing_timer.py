
import os
import datetime

from controller.algorithms.mixing_time.steps.preprocessor import Preprocessor
from controller.algorithms.mixing_time.steps.imageprocessor import ImageProcessor
from controller.algorithms.mixing_time.steps.extractor import Extractor

class MixingTimer:

    def __init__(self, resultpath, calibpath) -> None:

        self.resultpath = resultpath
        self.calibpath = calibpath
        
        self.calib = False

    def process_calibration(self) -> dict:
        
        try:
            # Preprocess the image
            preprocessor = Preprocessor(self.calibpath)
            self.calibimg = preprocessor.preprocess()

            # Process the calibration | We only want to do this once to save computational resources
            imageprocessor = ImageProcessor(self.calibimg)
            calibresult = imageprocessor.process()
            
            return calibresult

        except Exception as e:
            return None
        
    def process_images(self, path) -> dict:

        try:
            if not self.calib:
                self.calibresult = self.process_calibration()
                self.calib = True
            
            if self.calibresult is not None:
            
                # Preprocess
                preprocessor = Preprocessor(path)
                self.img = preprocessor.preprocess()
                
                # Process the image
                imageprocessor = ImageProcessor(self.img)
                self.imgresults = imageprocessor.process()

                rmetadata = self.imgresults.pop("Metadata")

                extractor = Extractor(result=self.imgresults, calibresult=self.calibresult)
                data = extractor.extract()

                name = os.path.basename(path)        

                return {
                    "Image": name,
                    "Timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                    "Metadata": rmetadata,
                    "Data": data
                }
            
            return None

        except Exception as e:
            return None