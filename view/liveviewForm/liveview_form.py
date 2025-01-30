
import cv2
import numpy as np
import time
from datetime import datetime

from PySide6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QPushButton, QFileDialog
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QImage, QPixmap, QCloseEvent, QIcon

from operator_mod.logger.global_logger import Logger
from operator_mod.eventbus.event_handler import EventManager
from controller.device_handler.devices.camera_device.camera import Camera
from controller.device_handler.devices.camera_device.states.all_states import LiveViewState

class LiveViewAcquisition(QThread):
    """Background thread for image capturing and converting. Two signals used for updating the live view and video capturing.
    """
    frame = Signal(QImage)
    raw_frame = Signal(np.ndarray)
    
    def __init__(self, camera):
        
        super().__init__()
        
        self.camera = camera
        self.running = False
        
    def run(self):
        self.running = True
        try:
            
            self.camera.stream_on()  # Start streaming
            while self.running:
                raw_img = self.camera.data_stream[0].get_image()
                rgb_image = raw_img.convert("RGB")
                numpy_image = rgb_image.get_numpy_array()
                frame = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)

                height, width, _ = frame.shape
                bytes_per_line = 3 * width
                q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)

                self.raw_frame.emit(numpy_image) # Emit raw frame for recording
                self.frame.emit(q_image)  # Emit the frame for GUI update
                time.sleep(0.0166) # 32 FPS
                
        except Exception as e:
            print(f"Error in LiveViewAcquisition thread: {e}")
        finally:
            self.camera.stream_off()  # Stop streaming when the thread stops

    def stop(self):
        self.running = False
        self.wait()  # Wait for the thread to finish
        
class LiveViewForm(QWidget):
    """
    Displays the live video feed from the camera (60FPS). 
    """
    def __init__(self) -> None:
        
        super().__init__()

        self.logger = Logger("Application").logger
        self.events = EventManager()
        self.camera = Camera.get_instance()
        
        self.acquisiton_thread = None
        self.video_writer = None
        self.recording = False
        
        # Event registration
        self.events.add_listener(self.events.EventKeys.LIVE_VIEW_STATE_ENTERED, self.live_view_start, 0, True)
        self.events.add_listener(self.events.EventKeys.LIVE_VIEW_STATE_TERMINATED, self.live_view_stop, 0, True)
        
        # Try to get camera object
        self.camera.add_task(self.camera.States.LIVE_VIEW_STATE, 0)
        self.cam_obj = self.camera.get_camera

    def setupForm(self):
        
        self.setWindowTitle("Live View")

        self.mainlayout = QVBoxLayout()
        self.setLayout(self.mainlayout)

        # The image window
        self.view = QGraphicsView(self)
        self.mainlayout.addWidget(self.view)

        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)

        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)
        
        # Video Recording
        self.video_button = QPushButton()
        self.video_button.setIcon(QIcon(r"view\liveviewForm\rec-button.png"))
        self.video_button.setCheckable(True)
        self.video_button.pressed.connect(self.toggle_recording)

        self.mainlayout.addWidget(self.video_button)

    def live_view_start(self):

        if not self.cam_obj:
            self.logger.warning("LiveView - Camera object not grabbable.")
            return
        
        try:
            self.acquisition_thread = LiveViewAcquisition(self.cam_obj)
            self.acquisition_thread.frame.connect(self.update_frame)
            self.acquisition_thread.raw_frame.connect(self.record_frame)
            self.acquisition_thread.start()
            
        except Exception as e:
            self.logger.error(f"Not able to start live View: {e}.")

    def live_view_stop(self):
        
        try:
            if self.acquisition_thread:
                self.acquisition_thread.stop()
                self.acquisition_thread = None
        except Exception:
            self.logger.info("LiveView Form alreadz terminated.")

    def toggle_recording(self):
        
        if self.recording is False:

            self.start_recording()
        
        elif self.recording is True:
                        
            self.stop_recording()

    def stop_recording(self):
        
        self.video_button.setIcon(QIcon(r"view\liveviewForm\rec-button.png"))

        ###
        if self.recording:
            self.recording = False
            
        if self.video_writer:
            self.video_writer.release()
            
    def start_recording(self):
        
        self.video_button.setIcon(QIcon(r"view\liveviewForm\stop-button.png"))
        
        ### Grabbing the path were to write to
        from view.main.mainframe import MainWindow
        mainwindow = MainWindow.get_instance()
        
        save_path, _ = QFileDialog.getSaveFileName(mainwindow,
        "Select Save Location",
        f"recording_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.avi",
        "AVI Files (*.avi);;All Files (*)")
        
        if not save_path:
            self.logger.warning("Incorrect video save path!")
            return
        
        ###
        # Setup the video writer
        self.video_writer = cv2.VideoWriter(
            save_path,
            cv2.VideoWriter_fourcc(*"XVID"),  # Codec
            32.0,  # FPS
            (3840, 2160)  # Frame size (match camera resolution)
        )
        
        self.logger.info(f"Recording started: {save_path}")
        self.recording = True
        
    def record_frame(self, img: np.ndarray):
        if self.recording and self.video_writer:
            self.video_writer.write(img)

    def update_frame(self, q_image: QImage):
        
        pixmap = QPixmap.fromImage(q_image)
        self.pixmap_item.setPixmap(pixmap)
        self.view.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatioByExpanding)

    def closeEvent(self, event: QCloseEvent):
        try:
            if self.acquisition_thread:
                self.acquisition_thread.stop()

            current = self.camera.get_current_state
            if current == LiveViewState:
                self.camera.stop()
                
        except Exception as e:
            self.logger.info(f"Live View - Closing Error: {e}")
        finally:
            from view.main.mainframe import MainWindow

            inst = MainWindow.get_instance()
            subwindows = inst.middle_layout.mdi_area.subWindowList()

            for subwindow in subwindows:
                if isinstance(subwindow.widget(), LiveViewForm):
                    inst.middle_layout.mdi_area.removeSubWindow(subwindow)

            event.accept()