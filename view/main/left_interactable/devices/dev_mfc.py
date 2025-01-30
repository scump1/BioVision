from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from operator_mod.logger.global_logger import Logger
from controller.device_handler.devices.mfc_device.mfc import MFC
from operator_mod.in_mem_storage.in_memory_data import InMemoryData

from model.data.configuration_manager import ConfigurationManager

class MFCWorker(QThread):
    
    progress_update = Signal(int, str)  # Signal to update progress bar and label
    finished = Signal(bool)             # Signal to indicate completion (success or failure)

    def __init__(self, target_massflow, data, mfc, logger):
        
        super().__init__()
        
        self.target_massflow = target_massflow
        self.data = data
        self.mfc = mfc
        self.logger = logger

    def run(self):
        try:
            # Update progress to "sending settings"
            self.progress_update.emit(15, "Sending settings to MFC...")
            self.data.add_data(self.data.Keys.MFC_SETTINGS, self.target_massflow, namespace=self.data.Namespaces.MFC)
            self.mfc.add_task(self.mfc.States.SETTING_SETTER_STATE, 0)

            # Update progress to "applying settings"
            self.progress_update.emit(45, "Applying MFC settings...")

            # Update progress to "checking settings"
            self.progress_update.emit(75, "Checking MFC settings...")

            timer = QElapsedTimer()
            timer.start()
            
            while timer.elapsed() < 2000:
                pass
            
            del timer

            success = self.data.get_data(self.data.Keys.CAMERA_DEVICE_SETTINGS_SUCCESS, self.data.Namespaces.CAMERA)

            if success:
                self.progress_update.emit(100, "Set settings successfully.")
                self.finished.emit(True)
            else:
                self.progress_update.emit(100, "Set settings unsuccessful.")
                self.finished.emit(False)

        except Exception as e:
            self.logger.warning(f"Could not set Settings to MFC: {e}")
            self.finished.emit(False)

class UIMFCWidget(QWidget):
    
    def __init__(self) -> None:
        
        super().__init__()
        
        self.data = InMemoryData()
        self.mfc = MFC.get_instance()
        self.logger = Logger("Application").logger
        
        self.configuration = ConfigurationManager.get_instance()
        
        self.massflow = None
        
        self.polltimer = QTimer()
        self.polltimer.setInterval(5000)
        self.polltimer.timeout.connect(self.poll_current_massflow)

    def setupWidget(self):
        self.setWindowTitle("MFC Settings")
        self.setContentsMargins(5,5,5,5)
        
        mainlayout = QVBoxLayout()
        
        self.formlayout = QFormLayout()
        
        # Current Massflow
        self.currentmassflow = QLabel(str(round(self.massflow))) if self.massflow else QLabel(str(0.0))
        self.formlayout.addRow("Current Massflow:", self.currentmassflow)

        # New Massflow
        self.massflow_box = QDoubleSpinBox()
        self.massflow_box.setRange(0.0, 50.0)
        self.massflow_box.setSingleStep(0.1)
        self.massflow_box.setValue(5.0)
        
        self.formlayout.addRow("Target Massflow:", self.massflow_box)
        
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
        
        self.polltimer.start()

    def apply_settings(self):
        
        # Disable UI and prepare progress bar
        self.formlayout.setEnabled(False)
        self.progressbar.setVisible(True)
        self.progress_label.setVisible(True)
        
        # Changing the config
        self.configuration.change_configuration(self.configuration.Devices.MFC, self.configuration.MFCSettings.MASSFLOW, self.massflow_box.value())
        
        # Start worker thread
        self.worker = MFCWorker(self.massflow_box.value(), self.data, self.mfc, self.logger)
        
        # Connect worker signals to update GUI
        self.worker.progress_update.connect(self.update_progress)
        self.worker.finished.connect(self.on_apply_finished)
        
        self.worker.start()  # Run the worker in a separate thread

    def update_progress(self, value, text):
        """Update progress bar and label text."""
        self.progressbar.setValue(value)
        self.progress_label.setText(text)


    def on_apply_finished(self, success):
        """Handle completion of apply settings."""
        if not success:
            self.progress_label.setStyleSheet("color: red;")
            self.progress_label.setText("Set settings unsuccessful.")
        
        else:
            self.progress_label.setText("Set settings successfully.")
    
        QTimer.singleShot(2000, self.reset_ui)
    
    def reset_ui(self):
        # Reset UI elements
        self.formlayout.setEnabled(True)
        self.progressbar.setVisible(False)
        self.progress_label.setVisible(False)
        self.progressbar.setValue(0)
        self.progress_label.setText('')
        self.progress_label.setStyleSheet('color: white;')
        self.adjustSize()

    def poll_current_massflow(self):
        """Polls the current massflow and updates the label."""
        try:
            self.mfc.add_task(self.mfc.States.READ_MASSFLOW_STATE, 0)

            self.update_massflow()
            
        except Exception as e:
            self.logger.warning(f"Coud not update massflow: {e}")

    def update_massflow(self):
        
        try:
            self.massflow = self.data.get_data(self.data.Keys.MFC_MASSFLOW, self.data.Namespaces.MFC)
            self.currentmassflow.setText(str(self.massflow))
        except Exception as e:
            self.logger.warning(f"Could not read MFC massflow: {e}")
    
    def closeEvent(self, event: QCloseEvent):
        try:
            if self.polltimer.isActive():
                self.polltimer.stop()
                
            from view.main.mainframe import MainWindow
            inst = MainWindow.get_instance()
            subwindows = inst.middle_layout.mdi_area.subWindowList()

            for subwindow in subwindows:
                if isinstance(subwindow.widget(), UIMFCWidget):
                    inst.middle_layout.mdi_area.removeSubWindow(subwindow)

        except Exception as e:
            self.logger.warning(f"Unclean subwindow exit in UI MFCWidget: {e}")
        
        finally:
            event.accept()
