
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *


from operator_mod.logger.global_logger import Logger
from controller.device_handler.devices.arduino_device.arduino import Arduino
from operator_mod.in_mem_storage.in_memory_data import InMemoryData


class UIArduinoWidget(QWidget):
    
    def __init__(self):
        
        super().__init__()
        
        self.data = InMemoryData()
        self.arudino = Arduino.get_instance()
        self.logger = Logger("Application").logger
        
    def setupForm(self):
        
        self.mainlayout = QVBoxLayout()
        
        self.maintabwidget = QTabWidget()
        
        ### The first widget: Lightswitch
        self.lightswitch_widget = QWidget()
        self.lighswitch_layout = QVBoxLayout()
        
        self.current_light_state_layout = QFormLayout()
        self.current_light_label = QLabel("Light: ")
        self.current_light_state = QLabel("OFF")

        self.current_light_state_layout.addRow(self.current_light_label, self.current_light_state)
        
        self.lightswitch_button = QPushButton("Switch")
        self.lightswitch_button.clicked.connect(self.lightswitch_button_action)
        
        self.lighswitch_layout.addLayout(self.current_light_state_layout)
        self.lighswitch_layout.addWidget(self.lightswitch_button)
        
        self.lightswitch_widget.setLayout(self.lighswitch_layout)
        
        ### Maybe temperature setter later        
        
        self.maintabwidget.addTab(self.lightswitch_widget, "Lightswitch")
        
        self.mainlayout.addWidget(self.maintabwidget)
        
        self.setLayout(self.mainlayout)
        
    def lightswitch_button_action(self):
        
        # This is a bit fishy but will work :)
        current_state = self.data.get_data(self.data.Keys.LIGHTMODE, self.data.Namespaces.MEASUREMENT)
        
        if type(current_state) is bool:
            self.data.add_data(self.data.Keys.LIGHTMODE, not current_state, self.data.Namespaces.MEASUREMENT)
            self.arudino.add_task(self.arudino.States.LIGHT_SWITCH_STATE, 0)
        
            self.current_light_state.setText("ON") if current_state == True else "OFF"
        
        elif current_state == None:
            # Then the light is OFF
            self.data.add_data(self.data.Keys.LIGHTMODE, True, self.data.Namespaces.MEASUREMENT)
            self.arudino.add_task(self.arudino.States.LIGHT_SWITCH_STATE, 0)
            
            self.current_light_state.setText("ON")
        
    def closeEvent(self, event):
        
        try:
            from view.main.mainframe import MainWindow
            inst = MainWindow.get_instance()
            subwindows = inst.middle_layout.mdi_area.subWindowList()

            for subwindow in subwindows:
                if isinstance(subwindow.widget(), UIArduinoWidget):
                    inst.middle_layout.mdi_area.removeSubWindow(subwindow)
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up ArduinoWidget: {e}.")