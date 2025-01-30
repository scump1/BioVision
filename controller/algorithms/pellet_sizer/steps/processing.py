
import cv2
from cv2.typing import *

class Processor:
    
    def __init__(self, img: MatLike):
        
        self.img = img
        
    def process(self):
        
        # Contours
        cont = self.contours(self.img)
        
        # Filtering the contours with shape & area
        filteredcont = self.filter(cont)
                
        return filteredcont
        
    # Functions
    def contours(self, img: MatLike) -> list:
        
        # Find contours and hierarchy
        conts, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        # Filter contours with no children -> pellets without internal defects or bubbles are excluded
        no_child_contours = [conts[i] for i in range(len(conts)) if hierarchy[0][i][2] == -1]

        return no_child_contours

    def filter(self, conts: list, len_thresh: int = 50, area_thresh: int  = 1000) -> list:
        
        filtered_cont = []
        
        for cont in conts:
            
            area = cv2.contourArea(cont)
        
            # First we take out small contours
            if len(cont) <= len_thresh:
                continue
            
            elif area < area_thresh: # as one pixel is roughly 0.55 µm 175 = 100µm
                continue
            
            _, _, w, h = cv2.boundingRect(cont)
            
            aspect_ratio = max(w, h) / min(w, h)
            if aspect_ratio > 2:
                continue
            
            area = cv2.contourArea(cont)
            extent = area / (w*h)
            
            if extent < 0.2:
                continue
            
            filtered_cont.append(cont)
            
        return filtered_cont