
import os

from controller.algorithms.pellet_sizer.steps.postprocessing import PostProcessing
from controller.algorithms.pellet_sizer.steps.preprocessing import Preprocessor
from controller.algorithms.pellet_sizer.steps.processing import Processor

class PelletSizer:
    
    def __init__(self) -> None:
        pass
    
    def processing(self, path : str, visualization: bool = False, settings : list = None) -> dict:
        """Processes a given pellet image to analzye for pellet sizes.

        Args:
            path (str): file path
            visualization (bool, optional): if an image should be returned. Defaults to False.
            settings (list, optional): a list of settings for individualization. Defaults to False.

        Raises:
            ValueError: If the path object does not exists.

        Returns:
            dict: "image" : Image if visualization, "Data" : data
        """
        
        self.path = path
        
        if not os.path.exists(path):
            raise ValueError("Path object does not exist in PelletSizer.") 
        
        # Preprocessing
        prepro = Preprocessor(self.path, settings)
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