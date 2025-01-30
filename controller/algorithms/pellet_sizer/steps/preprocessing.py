
import cv2
from cv2.typing import *

class Preprocessor():
    
    def __init__(self, path: str):
        
        self.path = path
        
    def process(self):
        
        # We load the image
        self.img = cv2.imread(self.path, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
        
        self.img = self.process_tile(self.img)
        
        return self.img
    
    def process_tile(self, tile) -> MatLike:
        
        tile = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
        
        tile = cv2.GaussianBlur(tile, (5,5), 0)
        
        _, tile = cv2.threshold(tile, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        
        return tile