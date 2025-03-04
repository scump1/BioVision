import time
import os
from uuid import uuid4

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

from operator_mod.measurements.mixing_time_handler import MixingTimeHandler

from controller.device_handler.devices.pump_device.pump import Pump

from operator_mod.logger.global_logger import Logger
from operator_mod.logger.progress_logger import ProgressLogger
from operator_mod.in_mem_storage.in_memory_data import InMemoryData

class UIMixingTime(QWidget):

    progress_signal = Signal(int, str)

    def __init__(self):
        
        super().__init__()
        
        self.data = InMemoryData()
        self.logger = Logger("Application").logger
        
        self.pump = Pump.get_instance()
        
        self.mixingtime_handler = MixingTimeHandler()
        
        self.progress_signal.connect(self._progressbar_update)
        
        # State switches
        self.calibration_done = False
        
    def setupForm(self):
    
        self.mainlayout = QVBoxLayout()
        self.stacked_layout = QStackedLayout()

        self.startpage = self.start_page()
        self.stacked_layout.addWidget(self.startpage)
        
        empty_reactor = self.empty_reactor_page()
        self.stacked_layout.addWidget(empty_reactor)
        
        fill_reactor = self.fill_reactor_page()
        self.stacked_layout.addWidget(fill_reactor)        
        
        start_mixing = self.start_mixing_page()
        self.stacked_layout.addWidget(start_mixing)
        
        self.mainlayout.addLayout(self.stacked_layout)
        
        ### Progressbar
        self.progressbar = QProgressBar()
        self.mainlayout.addWidget(self.progressbar)
        
        self.setLayout(self.mainlayout)

    def start_page(self) -> QWidget:
        
        mainwidget = QWidget()
        mainlayout = QVBoxLayout()
        mainlayout.setContentsMargins(5, 5, 5, 5)	

        naming_layout = QFormLayout()
        name_label = QLabel("Measurement Name: ")
        self.mt_name = QLineEdit()
        
        naming_layout.addRow(name_label, self.mt_name)
        
        mainlayout.addLayout(naming_layout)
        
        ### All the settings and informations needed
        settings_groupbox = QGroupBox()
        setting_layout = QGridLayout()
        
        ### For air massflow via the MFC
        massflow_label = QLabel("Air Massflow: ")
        self.massflow_value = QDoubleSpinBox()
        self.massflow_value.setRange(0, 70)
        self.massflow_value.setSingleStep(0.1)
        massflow_label_unit = QLabel("mL/min")
        
        ### Volume dispensing
        volume_label = QLabel("Dispensing Volume: ")
        self.volume_value = QSpinBox()
        self.volume_value.setRange(0, 2500)
        self.volume_value.setSingleStep(1)
        volume_label_unit = QLabel("µL")
        
        ### Add widgets to the grid layout
        setting_layout.addWidget(massflow_label, 0, 0)
        setting_layout.addWidget(self.massflow_value, 0, 1)
        setting_layout.addWidget(massflow_label_unit, 0, 2)
        
        setting_layout.addWidget(volume_label, 1, 0)
        setting_layout.addWidget(self.volume_value, 1, 1)
        setting_layout.addWidget(volume_label_unit, 1, 2)
        
        ### Other options
        self.result_show_option = QCheckBox("Show Results")
        setting_layout.addWidget(self.result_show_option, 2, 0, 1, 3)
        
        settings_groupbox.setLayout(setting_layout)
        mainlayout.addWidget(settings_groupbox)
        
        ### Start and Stop buttons
        self.start_button = QPushButton("Start setup routine")
        self.start_button.clicked.connect(self._start_routine_button_action)
        
        mainlayout.addWidget(self.start_button)
        mainwidget.setLayout(mainlayout)
        
        return mainwidget
    
    def empty_reactor_page(self) -> QWidget:
        
        empty_page = QWidget()
        empty_layout = QVBoxLayout()
        
        infotext = QLabel("Please emtpy the reactor of all liquids.")
        empty_layout.addWidget(infotext)
        
        checkbutton = QCheckBox("Reactor is empty")
        checkbutton.stateChanged.connect(lambda: self._empty_checbutton_action(checkbutton.isChecked()))
        empty_layout.addWidget(checkbutton)
        
        self.empty_reactor_fulfilled = QPushButton("Reactor is empty")
        self.empty_reactor_fulfilled.setEnabled(False)
        self.empty_reactor_fulfilled.clicked.connect(self._empty_ractor_button_action)
        empty_layout.addWidget(self.empty_reactor_fulfilled)
        
        empty_page.setLayout(empty_layout)
        
        return empty_page
        
    def fill_reactor_page(self) -> QWidget:
        
        fill_page = QWidget()
        fill_layout = QVBoxLayout()
        
        infotext = QLabel("Please fill the reactor with the desired liquid.")
        fill_layout.addWidget(infotext)
        
        checkbutton = QCheckBox("Reactor is filled")
        checkbutton.stateChanged.connect(lambda: self._filled_checbutton_action(checkbutton.isChecked()))
        fill_layout.addWidget(checkbutton)
        
        self.fill_reactor_fulfilled = QPushButton("Reactor is filled")
        self.fill_reactor_fulfilled.setEnabled(False)
        self.fill_reactor_fulfilled.clicked.connect(self._filled_reactor_button_action)
        fill_layout.addWidget(self.fill_reactor_fulfilled)
        
        fill_page.setLayout(fill_layout)
        
        return fill_page  
    
    def start_mixing_page(self) -> QWidget:
        
        start_mixing_page = QWidget()
        start_mixing_layout = QVBoxLayout()
        
        infotext = QLabel("The reactor is filled and the mixing process can start.")
        start_mixing_layout.addWidget(infotext)
        
        self.start_mixing_button = QPushButton("Start Mixing")
        self.start_mixing_button.clicked.connect(self._start_mixing_button_action)
        start_mixing_layout.addWidget(self.start_mixing_button)
        
        start_mixing_page.setLayout(start_mixing_layout)
        
        return start_mixing_page
    
    def _empty_checbutton_action(self, state: bool):
        self.empty_reactor_fulfilled.setEnabled(state)
    
    def _filled_checbutton_action(self, state: bool):
        self.fill_reactor_fulfilled.setEnabled(state)
    
    def _start_routine_button_action(self):
        
        from view.main.mainframe import MainWindow
        instance = MainWindow.get_instance()
            
        if self.mt_name.text() == "":
            QMessageBox.information(instance, "Error", "Please enter a name for the measurement.", QMessageBox.StandardButton.Ok)
            return
        
        if self.volume_value.value() == 0 or self.massflow_value.value() == 0:
            QMessageBox.information(instance, "Error", "Please enter a value for the volume and massflow.", QMessageBox.StandardButton.Ok)
            return
        
        self.startpage.setEnabled(False)
        self.progress_signal.emit(0, "Checking devices...")
        
        ### First we check if pumps and camera are available
        pump = self.data.get_data(self.data.Keys.PUMP, self.data.Namespaces.DEVICES)
        camera = self.data.get_data(self.data.Keys.CAMERA, self.data.Namespaces.DEVICES)
        
        if not pump or not camera:
            
            QMessageBox.information(instance, "Error", "Please connect a pump and a camera first.", QMessageBox.StandardButton.Ok)
            
            self.progress_signal.emit(0, "")
            self.startpage.setEnabled(True)
            return 
        
        self.progress_signal.emit(50, "Devices healthy...")
        self.progress_signal.emit(50, "Setting filestructures...")
        
        self.mixingtime_handler.setup_mixing_time_measurement(self.mt_name.text())
        
        self.progress_signal.emit(100, "Filestructures set...")
        time.sleep(1)
        
        self.stacked_layout.setCurrentIndex(1)
        self.progress_signal.emit(0, "")
    
    def _empty_ractor_button_action(self):
        
        ### Here we need to take the calibration pictures of the empty reactor
        self.progress_signal.emit(0, "Taking empty calibration images...")
        self.mixingtime_handler.take_empty_calibration()
        done = self._wait_for_empty_calibration()
        
        if not done:
            self._reset_mixing_time_routine()
            return
        
        # This means we have done a calibration and now flip back the flag to false
        self.calibration_done = False
        self.progress_signal.emit(100, "Empty calibration done...")
        time.sleep(2)
        
        self.stacked_layout.setCurrentIndex(2)
        self.progress_signal.emit(0, "")
        
    def _filled_reactor_button_action(self):
        
        ### We need to take the filled calibration pictures of the reactor
        self.progress_signal.emit(0, "Taking filled calibration images...")
        self.mixingtime_handler.take_filled_calibration()
        done = self._wait_for_filled_calibration()
        
        if not done:
            self._reset_mixing_time_routine()
            return
        
        # This means we have done a calibration and now flip back the flag to false
        self.calibration_done = False
        self.progress_signal.emit(100, "Filled calibration done...")
        time.sleep(2)
        
        self.stacked_layout.setCurrentIndex(3)
        self.progress_signal.emit(0, "")        
        
    def _start_mixing_button_action(self):
        """
        Exectues the last check-ups and start the mixing time runner thread.
        """
        fill_level_pump = self.pump.fill_level
        
        if fill_level_pump <= self.volume_value.value():
            from view.main.mainframe import MainWindow
            instance = MainWindow.get_instance()
            
            instance.menubar.actionDevicePump.trigger()
            QMessageBox.information(instance, "Pump Volume", "Please aspirate solution volume to inject into the reactor before starting the mixing time measurement.", QMessageBox.StandardButton.Yes)

            return
        
        # we start the runner here and start a timer to check the progress logger
        self.progress_signal.emit(0, "Starting mixing routine...")
        
        handle = str(uuid4())
        self.mixingtime_handler.start_mixing_time(handle, self.massflow_value.value(), self.volume_value.value())
        
        time.sleep(2)
        # the used progress tracker for the mixing time
        progress = ProgressLogger(handle)
        
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self._check_progress(progress))
        self.timer.start(1000)
    
    def _check_progress(self, progress: ProgressLogger):
        
        _, target, current = progress.get_progress('mixing_time')
    
        value = int((current / target) * 100)
        self.progress_signal.emit(value, "Mixing in progress...")
        
        if value == 100:
            self.progress_signal.emit(100, "Mixing done...")
            self.timer.stop()
    
    def _progressbar_update(self, value: int, text: str):
        self.progressbar.setValue(value)
        self.progressbar.setFormat(text)
        
    def _wait_for_empty_calibration(self, timeout: int = 30):
        
        while (self.calibration_done == False) and timeout >= 0:
            self.progress_signal.emit(30 - timeout, f"Waiting for calibration to finish... {timeout}") 
            
            path = self.data.get_data(self.data.Keys.EMPTY_CALIBRATION_IMAGE_PATH, self.data.Namespaces.MIXING_TIME)
            if path is not None and os.path.exists(path):
                self.calibration_done = True
                break

            timeout -= 1
            time.sleep(1)
            
        return self.calibration_done
    
    def _wait_for_filled_calibration(self, timeout: int = 30):
        
        while (self.calibration_done == False) and timeout >= 0:
            self.progress_signal.emit(30 - timeout, f"Waiting for calibration to finish... {timeout}")
            
            path = self.data.get_data(self.data.Keys.FILLED_CALIBRATION_IMAGE_PATH, self.data.Namespaces.MIXING_TIME)
            if path is not None and os.path.exists(path):
                self.calibration_done = True
                break

            timeout -= 1
            time.sleep(1)
            
        return self.calibration_done
    
    def _reset_mixing_time_routine(self) -> None:
        """
        This is meant for error catching. Not for actually resetting the routine.
        """
        from view.main.mainframe import MainWindow
        instance = MainWindow.get_instance()
            
        QMessageBox.warning(instance, "Error", "Something went wrong. Consult Leon...", QMessageBox.StandardButton.Ok)
        
        self.stacked_layout.setCurrentIndex(0)
        self._empty_checbutton_action(False)
        self._filled_checbutton_action(False)
    
    def closeEvent(self, event):
        
        try:
            if self.timer.isActive():
                self.timer.stop()

            from view.main.mainframe import MainWindow
            inst = MainWindow.get_instance()
            subwindows = inst.middle_layout.mdi_area.subWindowList()

            for subwindow in subwindows:
                if isinstance(subwindow.widget(), UIMixingTime):
                    inst.middle_layout.mdi_area.removeSubWindow(subwindow)

        except Exception as e:
            self.logger.warning(f"Unclean subwindow exit in UI MixingTime: {e}")
        
        finally:
            event.accept()
        