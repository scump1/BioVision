
import cv2
import cv2.typing

import numpy as np

class PostProcessing:

    def __init__(self, contours, img):
        
        self.img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        self.contours = contours
        
        self.result = []
        
    def postprocess(self):
        
        for i, contour in enumerate(self.contours):
            
            result = self.pellet_processor(contour, i+1)
            self.result.append(result)
        
        return self.result, self.img        
    
    def pellet_processor(self, contour, number: int) -> list:
        """Marks all pellets with a number and calculates the results."""

        # Puts a number to the pellets
        x, y, _, _ = cv2.boundingRect(contour)
        xi, yi = self.img.shape[0:2]
        
        larger_dimension = xi if xi > yi else yi
        
        if larger_dimension < 2500:
            font_size = 2
            font_thickness = 2
            
        elif larger_dimension < 5000:
            font_size = 4
            font_thickness = 10
        else:
            font_size = 15
            font_thickness = 20
        
        self.img = cv2.putText(self.img, str(number), (x, y), cv2.FONT_HERSHEY_PLAIN, font_size, (0,0,255), font_thickness, cv2.LINE_AA)
        
        # Draawing the contour
        self.img = cv2.drawContours(self.img, [contour], 0, (0,255,0), 2, cv2.LINE_AA)
        
        # Calculating properties
        area = cv2.contourArea(contour) 
        diameter = ( (area*4) / np.pi ) ** 0.5
        perimeter = diameter * np.pi

        results = [area, diameter, perimeter]
        
        return results