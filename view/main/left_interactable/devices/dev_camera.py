from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

from operator_mod.logger.global_logger import Logger
from controller.device_handler.devices.camera_device.camera import Camera
from operator_mod.in_mem_storage.in_memory_data import InMemoryData

from model.data.configuration_manager import ConfigurationManager

class CameraWorker(QThread):
    progress_update = Signal(int, str)  # Signal to update progress bar and label
    finished = Signal(bool)             # Signal to indicate completion (success or failure)

    def __init__(self, settings, data, camera, logger):
        super().__init__()
        self.settings = settings
        self.data = data
        self.camera = camera
        self.logger = logger
        self.success = False

    def run(self):
        try:

            # Step 1: Send settings to camera
            self.progress_update.emit(15, "Sending settings to camera...")
            self.data.add_data(self.data.Keys.CAMERA_DEVICE_SETTINGS, self.settings, self.data.Namespaces.CAMERA)

            # Step 2: Apply settings
            self.progress_update.emit(45, "Applying camera settings...")
            self.camera.add_task(self.camera.States.CUSTOM_SETTINGS_SETTER, 0)

            # Step 3: Verify settings
            self.progress_update.emit(75, "Checking camera settings")

            timer = QElapsedTimer()
            timer.start()
            
            # Check success status for a second
            while timer.elapsed() < 2000:
                self.success = self.data.get_data(self.data.Keys.CAMERA_DEVICE_SETTINGS_SUCCESS, self.data.Namespaces.CAMERA)
            
            del timer
            
            if self.success:
                self.progress_update.emit(100, "Set settings successfully.")
            else:
                self.progress_update.emit(0, "Set settings unsuccessful.")

        except Exception as e:
            self.logger.warning(f"Could not set custom Camera settings: {e}")
            self.success = False
        finally:
            self.finished.emit(self.success)

class UICameraWidget(QWidget):
    
    def __init__(self) -> None:
        super().__init__()
        
        self.data = InMemoryData()
        self.camera = Camera.get_instance()
        self.configuration = ConfigurationManager()
        self.logger = Logger("Application").logger
        self.progress_value = 0

    def setupWidget(self):
        
        values = self.configuration.get_configuration(self.configuration.Devices.CAMERA)
        
        autowhite, exposuretime, gain, saturation = list(values.values())
        
        self.setWindowTitle("Camera Settings")
        self.setContentsMargins(5,5,5,5)
        
        mainlayout = QVBoxLayout()
        
        # Form layout for camera settings
        self.formlayout = QFormLayout()
        
        # White balance setting
        self.autowhite_balance = QSpinBox()
        self.autowhite_balance.setRange(0, 1)
        self.autowhite_balance.setValue(autowhite)
        self.formlayout.addRow("Whitetone Autobalancing", self.autowhite_balance)

        # Exposure time setting
        self.exposuretime = QSpinBox()
        self.exposuretime.setRange(30, 10000)
        self.exposuretime.setValue(exposuretime)
        self.formlayout.addRow("Exposure Time [ms]", self.exposuretime)
        
        # Gain setting
        self.gain = QSpinBox()
        self.gain.setRange(0, 25)
        self.gain.setValue(gain)
        self.formlayout.addRow("Gain", self.gain)
        
        # Saturation setting
        self.saturation = QSpinBox()
        self.saturation.setRange(0, 100)
        self.saturation.setValue(saturation)
        self.formlayout.addRow("Saturation", self.saturation)
        
        mainlayout.addLayout(self.formlayout)
        
        # Apply button and progress bar
        self.applybutton = QPushButton("Apply")
        self.applybutton.pressed.connect(self.apply_settings)
        
        self.progressbar = QProgressBar()
        self.progressbar.setRange(0, 100)
        self.progressbar.setValue(0)
        self.progressbar.setVisible(False)
        
        self.progress_label = QLabel()
        self.progress_label.setVisible(False)

        mainlayout.addWidget(self.applybutton)
        mainlayout.addWidget(self.progressbar)
        mainlayout.addWidget(self.progress_label)
        
        self.setLayout(mainlayout)
        
    def apply_settings(self):
        
        # Disable UI and initialize progress bar
        self.formlayout.setEnabled(False)
        self.progressbar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_label.setText("Initializing...")
        self.progress_value = 0
        self.progressbar.setValue(self.progress_value)

        # Collect settings
        settings = [
            self.autowhite_balance.value(),
            self.exposuretime.value(),
            self.gain.value(),
            self.saturation.value()
        ]

        # Start the worker thread
        self.worker = CameraWorker(settings, self.data, self.camera, self.logger)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.finished.connect(self.on_apply_finished)
        
        # Start a QTimer for smooth progress bar updates
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.increment_progress)
        self.progress_timer.start(100)

        self.worker.start()  # Begin processing in the background

    def update_progress(self, value, message):
        """Update progress bar and label text based on worker signals."""
        self.progressbar.setValue(value)
        self.progress_label.setText(message)
        if value == 100:
            self.progress_timer.stop()  # Stop timer when complete

    def increment_progress(self):
        """Incremental progress bar update to smooth out the UI experience."""
        if self.progress_value < 100:
            self.progress_value = min(100, self.progress_value + 5)
            self.progressbar.setValue(self.progress_value)

    def on_apply_finished(self, success):
        """Handle completion of apply settings."""
        self.progress_timer.stop()  # Stop the progress timer
        self.progressbar.setValue(100)  # Ensure progress bar is full

        # Update the label to indicate success or failure
        if success:
            self.progress_label.setText("Set settings successfully.")
        else:
            self.progress_label.setStyleSheet("color: red;")
            self.progress_label.setText("Set settings unsuccessful.")

        # Reset UI elements after a brief delay
        QTimer.singleShot(2000, self.reset_ui)

    def reset_ui(self):
        """Reset UI elements after task completion."""
        self.formlayout.setEnabled(True)
        self.progressbar.setVisible(False)
        self.progress_label.setVisible(False)
        self.progressbar.setValue(0)
        self.progress_label.setText('')
        self.progress_label.setStyleSheet('color: black;')

    def closeEvent(self, event: QCloseEvent):
        try:
            if self.progressbar.value() > 0:
                event.ignore()
                return
            
            from view.main.mainframe import MainWindow
            inst = MainWindow.get_instance()
            subwindows = inst.middle_layout.mdi_area.subWindowList()

            for subwindow in subwindows:
                if isinstance(subwindow.widget(), UICameraWidget):
                    inst.middle_layout.mdi_area.removeSubWindow(subwindow)

        except Exception as e:
            self.logger.warning(f"Unclean subwindow exit in UICameraWidget: {e}")
        
        finally:
            event.accept()
