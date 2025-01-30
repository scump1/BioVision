from PySide6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap, QResizeEvent
import cv2

class ImageDisplay(QWidget):
    
    def __init__(self, image: str | list):
        """A view on an image.

        Args:
            image (str | MatLike): path to an image or the iamge itself
        """
        super().__init__()
        
        self.img = None
        self.img_item = None
        self.path = None
        
        if type(image) is str:
                    
            self.path = image
            self.img = cv2.imread(image, cv2.IMREAD_ANYCOLOR | cv2.IMREAD_ANYDEPTH)
            
        else:
            self.img = image
        
    def setupForm(self) -> QWidget:
        
        mainlayout = QVBoxLayout()
        
        self.graphicsview = QGraphicsView()
        self.graphicsview.setBaseSize(150, 450)
        self.graphicsview.setContentsMargins(5, 5, 5, 5)
        
        self.img_scene = QGraphicsScene()
        self.graphicsview.setScene(self.img_scene)

        self.img_item = QGraphicsPixmapItem()
        self.img_scene.addItem(self.img_item)
        
        if self.img is not None:
            # Normalize the 12-bit image to 8-bit
            if self.img.dtype == 'uint16':
                # Assuming the image is 12-bit
                self.img = (self.img / 16).astype('uint8')
                
            # Convert the image from BGR (OpenCV) to RGB (Qt)
            image = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)

            # Making the image accessible for Qt
            height, width, _ = image.shape
            bytes_per_line = 3 * width
            q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)

            pixmap = QPixmap.fromImage(q_image)
            self.img_item.setPixmap(pixmap)

            self.graphicsview.fitInView(self.img_item, Qt.AspectRatioMode.KeepAspectRatio)
              
        mainlayout.addWidget(self.graphicsview)
        self.setLayout(mainlayout)
        
        return self
    
    def resizeEvent(self, event: QResizeEvent):
        """Resize event to automatically fit the image to the widget."""
        
        super().resizeEvent(event)
        if self.img_item and not self.img_item.pixmap().isNull():
            self.graphicsview.fitInView(self.img_item, Qt.AspectRatioMode.KeepAspectRatio)
      
    def set_image(self, image: str | list) -> None:
        """Setting a new image into the display. 

        Args:
            image (str | list): str if path or np.array(list) if direct image
        """
        if type(image) is str:
            self.img = cv2.imread(image, cv2.IMREAD_ANYDEPTH | cv2.IMREAD_ANYCOLOR)
        
        else:
            self.img = image
        
        if self.img is not None:
            # Normalize the 12-bit image to 8-bit
            if self.img.dtype == 'uint16':
                # Assuming the image is 12-bit
                self.img = (self.img / 16).astype('uint8')
                
            # Convert the image from BGR (OpenCV) to RGB (Qt)
            image = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)

            # Making the image accessible for Qt
            height, width, _ = image.shape
            bytes_per_line = 3 * width
            q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)

            pixmap = QPixmap.fromImage(q_image)
            self.img_item.setPixmap(pixmap)

            self.graphicsview.fitInView(self.img_scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
              