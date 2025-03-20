from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

from operator_mod.logger.global_logger import Logger
from controller.device_handler.devices.mfc_device.mfc import MFC
from operator_mod.in_mem_storage.in_memory_data import InMemoryData

from model.data.configuration_manager import ConfigurationManager

class UIMFCWidget(QWidget):
    
    massflow_set = Signal()
    
    def __init__(self) -> None:
        
        super().__init__()
        
        self.data = InMemoryData()
        self.mfc = MFC.get_instance()
        self.logger = Logger("Application").logger
        
        self.data.add_data(self.data.Keys.MFC_DEVICE_UI_REFERENCE, self, self.data.Namespaces.PROJECT_MANAGEMENT)
        
        self.configuration = ConfigurationManager.get_instance()
        
        self.massflow_set.connect(self.on_apply_finished)
        
        self.massflow : float = None
        self.valve_status : bool = True
        
        self.polltimer = QTimer()
        self.polltimer.setInterval(1000)
        self.polltimer.timeout.connect(self.poll_current_massflow)

    def setupWidget(self):
        
        self.setWindowTitle("MFC Settings")
        self.setContentsMargins(5,5,5,5)
        
        mainlayout = QVBoxLayout()
        
        # Status Layout
        status_layout = QGridLayout()
        
        # The current status
        
        massflow_label = QLabel('Current Massflow: ')
        valve_status_label = QLabel('Valve Status')
        
        self.currentmassflow = QLabel(str(round(self.massflow))) if self.massflow else QLabel(str(0.0))
        self.current_valve_status = QLabel('Open')
        
        status_layout.addWidget(massflow_label, 0, 0, Qt.AlignmentFlag.AlignLeft)
        status_layout.addWidget(self.currentmassflow, 0, 1, Qt.AlignmentFlag.AlignLeft)
        
        status_layout.addWidget(valve_status_label, 1, 0, Qt.AlignmentFlag.AlignLeft)
        status_layout.addWidget(self.current_valve_status, 1, 1, Qt.AlignmentFlag.AlignLeft)
        
        mainlayout.addLayout(status_layout)
        
        ### Tab Widget as background
        maintabwidget = QTabWidget()
        mainlayout.addWidget(maintabwidget)
        
        ## Layout for Opening / CLosing the Valve
        open_close_widget = QWidget()
        open_close_layout = QVBoxLayout()

        description_label = QLabel('Close the Valve of the MFC completely.')
        description_label2 = QLabel('Reopnenig the Valve sets the last known massflow target.')
        
        self.open_close_button = QPushButton('Close')
        self.open_close_button.clicked.connect(self._open_close_valve)
        
        open_close_layout.addWidget(description_label)
        open_close_layout.addWidget(description_label2)
        open_close_layout.addWidget(self.open_close_button)
        
        open_close_widget.setLayout(open_close_layout)
        
        maintabwidget.addTab(open_close_widget, 'Open / Close')
        
        ## New Massflow Setter
        massflow_set_Widget = QWidget()
        massflow_set_layout = QVBoxLayout()
        
        massflow_set_Widget.setLayout(massflow_set_layout)
        
        self.formlayout = QFormLayout()
        
        massflow_set_layout.addLayout(self.formlayout)
        
        # New Massflow
        self.massflow_box = QDoubleSpinBox()
        self.massflow_box.setRange(0.0, 50.0)
        self.massflow_box.setSingleStep(0.1)
        self.massflow_box.setValue(5.0)
        
        self.formlayout.addRow("Target Massflow:", self.massflow_box)
                
        # Apply button and progress bar
        self.applybutton = QPushButton("Apply")
        self.applybutton.pressed.connect(self.apply_settings)
        
        self.progressbar = QProgressBar()
        self.progressbar.setRange(0, 100)
        self.progressbar.setValue(0)
        
        self.progress_label = QLabel()

        massflow_set_layout.addWidget(self.applybutton)
        massflow_set_layout.addWidget(self.progressbar)
        massflow_set_layout.addWidget(self.progress_label)
        
        maintabwidget.addTab(massflow_set_Widget, 'Massflow Control')
        
        self.setLayout(mainlayout)
        
        self.polltimer.start()

    def apply_settings(self):
        
        # Disable UI and prepare progress bar
        self.formlayout.setEnabled(False)
        
        self.update_progress(20, 'Applying settings...')
        
        # Changing the config
        self.configuration.change_configuration(self.configuration.Devices.MFC, self.configuration.MFCSettings.MASSFLOW, self.massflow_box.value())
        
        # Start worker thread
        self.data.add_data(self.data.Keys.MFC_SETTINGS, self.massflow_box.value(), self.data.Namespaces.MFC)
        self.mfc.add_task(self.mfc.States.SETTING_SETTER_STATE, 0)

    def update_progress(self, value : int, text : str):
        """Update progress bar and label text."""
        self.progressbar.setValue(value)
        self.progress_label.setText(text)


    def on_apply_finished(self):
        """Handle completion of apply settings."""
        
        success = self.data.get_data(self.data.Keys.MFC_SETTINGS_SUCCESS, self.data.Namespaces.MFC)
        
        if success:
            self.update_progress(100, 'Successful.')
        else:
            self.progress_label.setStyleSheet('color: red;')
            self.update_progress(100, 'Unsuccessful.')
    
        QTimer.singleShot(2000, self.reset_ui)
    
    def reset_ui(self):
        # Reset UI elements
        self.formlayout.setEnabled(True)
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
            self.currentmassflow.setText(f"{self.massflow:.2f}")
        except Exception as e:
            self.logger.warning(f"Could not read MFC massflow: {e}")
    
    def _open_close_valve(self):
        
        # From opnening to closing
        if self.valve_status == True:
            self.mfc.add_task(self.mfc.States.CLOSE_VALVE, 0)
            self.valve_status = False
            
            self.open_close_button.setText('Reopen')
            self.current_valve_status.setText('Closed')
            

        elif self.valve_status == False:
            self.mfc.add_task(self.mfc.States.OPEN_VALVE, 0)
            self.valve_status = True
            
            self.open_close_button.setText('Close')
            self.current_valve_status.setText('Opened')

    
    def closeEvent(self, event: QCloseEvent):
        try:
            
            if self.polltimer is not None:
                if self.polltimer.isActive():
                    self.polltimer.stop()
                
            from view.main.mainframe import MainWindow
            inst = MainWindow.get_instance()
            subwindows = inst.middle_layout.mdi_area.subWindowList()

            for subwindow in subwindows:
                if isinstance(subwindow.widget(), UIMFCWidget):
                    inst.middle_layout.mdi_area.removeSubWindow(subwindow)

            self.data.delete_data(self.data.Keys.MFC_DEVICE_UI_REFERENCE, self.data.Namespaces.PROJECT_MANAGEMENT)

        except Exception as e:
            self.logger.warning(f"Unclean subwindow exit in UI MFCWidget: {e}")
        
        finally:
            event.accept()
