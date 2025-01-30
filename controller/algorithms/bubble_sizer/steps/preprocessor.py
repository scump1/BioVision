import cv2
import os

class Preprocessor:
    """Preprocesses a given image for the Bubble Sizer Pipeline. Returns a img (MatLike) for further processing."""

    def __init__(self, path, calibpath = None) -> None:
        
        self.imgpath = path

        self.calibpath = calibpath

        if os.path.exists(self.imgpath):
            self.img = cv2.imread(self.imgpath, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
        
        else:
            return
        
        if self.calibpath is not None:
            if os.path.exists(self.calibpath):
                self.calibimg = cv2.imread(self.calibpath, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)

    def preprocess(self) -> cv2.Mat:

        # If we have a calibration image we take it as background substract else we do it normally
        if self.calibpath is not None:

            # Step 1: Convert to grayscale
            self.calib_converter()
            
            # Step 2: Denoising, demosaicing
            self.calib_enhance()
            
            # Step 3: Substract img from another
            self.calib_calibrate()

            # Step 4: Binarize
            self.binarize()

        else:
            
            self.normal_converter()
            
            self.normal_enhance()
            
            self.binarize()
            
        return self.img
    
    ### This is without calibration image
    def normal_converter(self) -> None:
        """Determines colorspace and converts accordingly."""
        self.img = cv2.cvtColor(self.img, cv2.COLOR_RGB2GRAY)
        
    def normal_enhance(self) -> None:
        """Does basic image enhancement."""
        self.img = cv2.GaussianBlur(self.img, (5,5), 0)

    ### This is for having a calibration image
    def calib_converter(self) -> None:
        """Determines colorspace and converts accordingly."""
        self.img = cv2.cvtColor(self.img, cv2.COLOR_RGB2GRAY)
        self.calibimg = cv2.cvtColor(self.calibimg, cv2.COLOR_RGB2GRAY)

    def calib_enhance(self) -> None:
        """Does basic image enhancement."""
        self.img = cv2.fastNlMeansDenoising(self.img, None, 10, 7, 21)        
        self.calibimg = cv2.fastNlMeansDenoising(self.calibimg, None, 10, 7, 21)

    def calib_calibrate(self) -> None:

        # Subtract the images
        self.img = cv2.absdiff(self.calibimg, self.img)
        self.img = cv2.bitwise_not(self.img)

    def binarize(self) -> None:
        """Image Binarization"""
        _, self.img = cv2.threshold(self.img, 0, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)