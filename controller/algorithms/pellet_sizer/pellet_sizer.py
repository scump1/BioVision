
import os

from controller.algorithms.pellet_sizer.steps.postprocessing import PostProcessing
from controller.algorithms.pellet_sizer.steps.preprocessing import Preprocessor
from controller.algorithms.pellet_sizer.steps.processing import Processor

class PelletSizer:
    
    def __init__(self) -> None:
        pass
    
    def processing(self, path : str, visualization: bool = False) -> dict:
        
        self.path = path
        
        if not os.path.exists(path):
            raise ValueError("Path object does not exist in PelletSizer.") 
        
        # Preprocessing
        prepro = Preprocessor(self.path)
        img = prepro.process()
        
        # Processing
        pro = Processor(img)
        contours = pro.process()
        
        # Postprocessing
        post = PostProcessing(contours, img)
        results, image = post.postprocess()
        
        if visualization:
            return {
                "Image": image,
                "Data": results
            }
            
        else:
            return {
                "Data": results
                }