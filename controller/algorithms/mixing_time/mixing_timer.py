
import cv2
import os

from controller.algorithms.mixing_time.steps.preprocessor import Preprocessor
from controller.algorithms.mixing_time.steps.processor import Processor

class MixingTimer:
    
    def __init__(self, empty_calibration: str, full_calibration: str, local_mixing_time : bool = False):

        self.local_mixing_time = local_mixing_time
        
        if os.path.exists(empty_calibration) and os.path.exists(full_calibration):
            self.empty_calibration = cv2.imread(empty_calibration) 
            self.full_calibration = cv2.imread(full_calibration)
            
        else:
            return

        ### First the preprocessing of the calibrations
        self.prepro = Preprocessor(self.empty_calibration, self.full_calibration)
        mask = self.prepro.preprocess_calibration()
        
        self.mask = mask

    def process_image(self, image: str):

        np_image = cv2.imread(image)
        np_image = cv2.cvtColor(np_image, cv2.COLOR_BGR2RGB)
        
        np_image = self.prepro.preprocess_image(np_image)
        
        processor = Processor(self.mask)

        tiles = None
        if self.local_mixing_time:
            # we dynimcally tile the image
            tiles, tile_size, tilenumbers = self.prepro.dynamic_tiling(np_image, self.mask)            
            tile_data = processor.process_local(tiles, tilenumbers)

        g_variance, g_entropy = processor.process(np_image)
        
        ### postprocessing TBD
        # We want to retrieve visualizations directly? Or just data?
        # postprocessor = Postprocessor()
        # postprocessor.postprocess()
        
        if self.local_mixing_time:
            return g_variance, g_entropy, tile_size, tilenumbers, tile_data
        else:
            return g_variance, g_entropy