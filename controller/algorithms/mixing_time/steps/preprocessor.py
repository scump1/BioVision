
import cv2

class Preprocessor:

    def __init__(self, path):
        
        self.imgpath = path

        self.img = cv2.imread(self.imgpath, cv2.IMREAD_COLOR | cv2.IMREAD_ANYDEPTH)

    def preprocess(self):

        # Step 2: Enahncing a bit
        self.enhance()

        return self.img
    
    def enhance(self):
        """Does basic image enhancement"""
        self.img = cv2.GaussianBlur(self.img, (5,5), 5)