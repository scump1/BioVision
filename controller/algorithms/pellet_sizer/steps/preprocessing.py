
import cv2
from cv2.typing import *

class Preprocessor():
    
    def __init__(self, path: str, settings : list = None):
        """Takes the path and settings

        Args:
            path (str): string path object
            settings (list, optional): [thresh_value, blur]. Defaults to None.
        """
        self.path = path
        self.settings = settings
        
    def process(self):
        
        # We load the image
        img = cv2.imread(self.path, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
        
        img = self.process_tile_with_settings(img)
        
        return img
    
    def process_tile_with_settings(self, img) -> MatLike:
        
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # The defeault settings list is just empty
        if self.settings != []:
            
            if self.settings[1] == "Gaussian":
                img = cv2.GaussianBlur(img, (5,5), 0)
                
            elif self.settings[1] == "Median":
                img = cv2.medianBlur(img, (5,5), 0)
                
            elif self.settings[1] == "Stacked":
                img = cv2.stackBlur(img, (5,5), 0)
            
            if self.settings[0] >= 0 :
                _, img = cv2.threshold(img, self.settings[0], 255, cv2.THRESH_BINARY_INV)
            elif self.settings[0] < 0:
                _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        
        else:
            img = cv2.GaussianBlur(img, (5,5), 0)
            _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        
        return img