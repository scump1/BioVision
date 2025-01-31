import time

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

from operator_mod.measurements.mixing_time_handler import MixingTimeHandler

from operator_mod.logger.global_logger import Logger
from operator_mod.in_mem_storage.in_memory_data import InMemoryData

class UIMixingTime(QWidget):

    progress_signal = Signal(int, str)

    def __init__(self):
        super().__init__()
        
        self.data = InMemoryData()
        self.logger = Logger("Application").logger
        
        self.mixingtime_handler = MixingTimeHandler()
        
        self.progress_signal.connect(self._progressbar_update)
        
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
        name_label = QLabel("Name: ")
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
        
        # if not pump or not camera:
            
        #     QMessageBox.information(instance, "Error", "Please connect a pump and a camera first.", QMessageBox.StandardButton.Ok)
            
        #     self.progress_signal.emit(0, "")
        #     self.startpage.setEnabled(True)
        #     return 
        
        self.progress_signal.emit(50, "Devices healthy...")
        self.progress_signal.emit(50, "Setting filestructures...")
        
        self.mixingtime_handler.setup_mixing_time_measurement(self.mt_name.text())
        
        self.progress_signal.emit(100, "Filestructures set...")
        time.sleep(1)
        
        self.stacked_layout.setCurrentIndex(1)
    
    def _empty_ractor_button_action(self):
        
        self.stacked_layout.setCurrentIndex(2)
        
    def _filled_reactor_button_action(self):
        
        self.stacked_layout.setCurrentIndex(3)
        
    def _start_mixing_button_action(self):
        pass
    
    def _progressbar_update(self, value: int, text: str):
        self.progressbar.setValue(value)
        self.progressbar.setFormat(text)
    
    def closeEvent(self, event):
        
        try:

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
        