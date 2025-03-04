
import numpy as np
import cv2
from cv2.typing import MatLike

class Preprocessor:
    
    def __init__(self, empty_calibration: MatLike, full_calibration: MatLike):
        
        self.empty_calibration = cv2.cvtColor(empty_calibration, cv2.COLOR_BGR2RGB) 
        self.full_calibration = cv2.cvtColor(full_calibration, cv2.COLOR_BGR2RGB) 
    
    def preprocess_calibration(self) -> MatLike:
        """Retrieves a mask of changed pixels over two calibration images. Does basic image enhancing.

        Returns:
            MatLike: the mask to be applied to further images.
        """
    
        # this represents the difference between the empty and full calibration images
        diff = cv2.absdiff(self.empty_calibration, self.full_calibration)
        diff = cv2.GaussianBlur(diff, (5,5), 0)
        
        # grayscale and thresholding
        gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray_diff, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        
        # Mask refining
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        return mask
    
    def dynamic_tiling(self, image: np.ndarray, mask: np.ndarray, tile_size: int = 32):
        """
        Dynamically determines tile size and splits the masked region of the image into tiles.
        
        Parameters:
            image (np.ndarray): The input image (H, W, C).
            mask (np.ndarray): The binary mask (H, W), where nonzero values indicate the region of interest.
            tile_size (int): Desired tile size (default 32), adjusted dynamically if needed.

        Returns:
            tiles (list): List of tiles (each tile as a CuPy array).
            tile_size (int): Final tile size used.
            n_tiles (tuple): Number of tiles in (x, y) directions.
        """
        # Handle empty mask case
        if not np.any(mask):
            return [], tile_size, (0, 0)

        # Find bounding box of masked region
        coords = np.argwhere(mask)
        y_min, x_min = coords.min(axis=0)
        y_max, x_max = coords.max(axis=0) + 1
        
        # Crop image and mask
        cropped_img = image[y_min:y_max, x_min:x_max]
        cropped_mask = mask[y_min:y_max, x_min:x_max]

        # Determine dimensions
        H, W = cropped_mask.shape

        # Adjust tile size based on both H and W, targeting at least 4 tiles
        area = H * W
        num_tiles_target = max(4, area // (tile_size ** 2))
        tile_size = max(9, int(np.sqrt(area / num_tiles_target)))

        # Calculate number of tiles
        n_tiles_y = max(1, (H + tile_size - 1) // tile_size)  # Ceiling division
        n_tiles_x = max(1, (W + tile_size - 1) // tile_size)

        # Compute tile heights and widths
        tile_h = [tile_size] * n_tiles_y
        tile_w = [tile_size] * n_tiles_x
        
        if H % tile_size != 0:
            tile_h[-1] = H - (tile_size * (n_tiles_y - 1))
        if W % tile_size != 0:
            tile_w[-1] = W - (tile_size * (n_tiles_x - 1))

        # Split image into tiles
        tiles = []
        y_start = 0
        for h in tile_h:
            x_start = 0
            for w in tile_w:
                tile = cropped_img[y_start:y_start + h, x_start:x_start + w]
                tiles.append(tile)  # Convert to CuPy array
                x_start += w
            y_start += h
        
        return tiles, tile_size, (n_tiles_x, n_tiles_y)

    def preprocess_image(self, image: str) -> MatLike:
        """Preprocesses an image by applying the mask and converting it to HSV.

        Args:
            image (MatLike): The image to be preprocessed.

        Returns:
            MatLike: The preprocessed image.
        """
        image = cv2.GaussianBlur(image, (5,5), 0)
    
        return image