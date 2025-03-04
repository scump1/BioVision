
from cv2.typing import MatLike
import cv2
from scipy.stats import entropy
import numpy as np

class Processor:
    
    def __init__(self, mask: MatLike, local: bool = False):
        
        self.mask = mask
        self.local = local # Flag for the local mixing time calculations
        
    def process(self, image: MatLike) -> tuple[list, list]:
        
        ### Global mixing time
        # We calculate variance and entropy

        g_variance, g_entropy = self.calculate_variance_entropy(image)

        return g_variance, g_entropy
    
    def process_local(self, tiles : list[MatLike], tilenumbers : tuple) -> dict:
        
        tile_data = {}
        
        tile_number_x, _ = tilenumbers
        
        i = 0
        j = 0
        
        for tile in tiles:
            
            l_variance = np.var(tile)
            
            # Compute entropy
            hist, _ = np.histogram(tile, bins=256, range=(0, 256), density=True)
            l_entropy = entropy(hist + 1e-9)  # Avoid log(0)

            tile_data[(i, j)] = [l_variance, l_entropy]
            
            i += 1
            
            if i == tile_number_x:
                j += 1
                i = 1

        return tile_data
    
    def calculate_variance_entropy(self, img: MatLike):
        """
        Calculate variance of pixel values over time.
        
        Returns:
            List of variance over time, List of entropy over time
        """

        if self.mask is not None:
            masked_img = img[self.mask > 0]
        else:
            masked_img = img

        g_variance = np.var(masked_img)
        
        hist, _ = np.histogram(masked_img, bins=256, range=(0, 256), density=True)
        g_entropy = entropy(hist + 1e-9)  # Adding small value to avoid log(0)
            
        return g_variance, g_entropy
