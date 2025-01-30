import os
import cv2

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QHBoxLayout, QWidget, QTabWidget
from PySide6.QtGui import QImage, QPixmap, QCloseEvent
from PySide6.QtCore import Qt

class ImageViewer(QWidget):

    def __init__(self, path) -> None:

        super().__init__()

        self.path = path
        self.filename = os.path.basename(path)

    def setupForm(self):

        self.setWindowTitle(f"Image: {self.filename}")

        self.mainlayout = QHBoxLayout()
        self.setLayout(self.mainlayout)

        self.wrapper_tab = QTabWidget()

        self.imageview = QGraphicsView()
        self.imageview.setContentsMargins(5,5,5,5)

        self.wrapper_tab.addTab(self.imageview, "Image")

        self.mainlayout.addWidget(self.wrapper_tab)

        self.img_scene = QGraphicsScene()
        self.imageview.setScene(self.img_scene)

        self.img_item = QGraphicsPixmapItem()
        self.img_scene.addItem(self.img_item)

        # Loading the actual image with 16-bit depth
        image = cv2.imread(self.path, cv2.IMREAD_ANYDEPTH | cv2.IMREAD_COLOR)
        
        # Normalize the 12-bit image to 8-bit
        if image is not None and image.dtype == 'uint16':
            # Assuming the image is 12-bit
            image = (image / 16).astype('uint8')

        # Convert the image from BGR (OpenCV) to RGB (Qt)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Making the image accessible for Qt
        height, width, _ = image.shape
        bytes_per_line = 3 * width
        q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)

        self.pixmap = QPixmap.fromImage(q_image)
        self.img_item.setPixmap(self.pixmap)

        self.imageview.fitInView(self.img_scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatioByExpanding)
        
    def closeEvent(self, event: QCloseEvent):
        
        try:
            # We gracefully remove the subwindow ehwn its closed here
            from view.main.mainframe import MainWindow

            inst = MainWindow.get_instance()
            subwindows = inst.middle_layout.mdi_area.subWindowList()

            for subwindow in subwindows:
                if isinstance(subwindow.widget(), self):
                    widget = subwindow.widget()
                    if widget.path == self.path:
                        inst.middle_layout.mdi_area.removeSubWindow(subwindow)
            
        except Exception as e:
            pass
        finally:
            event.accept()