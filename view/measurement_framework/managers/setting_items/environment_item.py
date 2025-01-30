
from PySide6.QtWidgets import *

from model.measurements.routine_system.routine_system import RoutineData, RoutineSystem

class EnvironmentItemWidget(QWidget):
    
    def __init__(self, routinesystem, slot):
        
        super().__init__()
        
        self.slot = slot

        self.routine: RoutineSystem = routinesystem
        
        self.lightmodes = {
            "Always On": RoutineData.LightMode.ALWAYS_ON,
            "On when needed": RoutineData.LightMode.ON_WHEN_NEEDED,
            "Always Off": RoutineData.LightMode.ALWAYS_OFF
        }
        
        self.first_init = True
        
        self.setupWidget()
        self.add_setting()
        
        self.first_init = False
        
    def setupWidget(self):
        
        mainlayout = QHBoxLayout()
        
        environment_label = QLabel("Environment")
        mainlayout.addWidget(environment_label)
        
        # Temperature
        temp_layout = QVBoxLayout()
        temp_label = QLabel("Temperature")
        
        temp_unit = QComboBox()
        temp_unit.addItems(["°C"])
        
        self.temp_value = QDoubleSpinBox()
        self.temp_value.setRange(0, 50)
        self.temp_value.valueChanged.connect(self.add_setting)
        
        temp_layout.addWidget(temp_label)
        temp_layout.addWidget(temp_unit)
        temp_layout.addWidget(self.temp_value)
        
        mainlayout.addLayout(temp_layout)
        
        # Lightmode
        light_layout = QVBoxLayout()
        light_label = QLabel("Light Mode")
        
        self.light_modes_box = QComboBox()
        self.light_modes_box.addItems(["Always On", "On when needed", "Always Off"])
        self.light_modes_box.currentTextChanged.connect(self.add_setting)
        
        light_layout.addWidget(light_label)
        light_layout.addWidget(self.light_modes_box)
        
        mainlayout.addLayout(light_layout)
        
        self.setLayout(mainlayout)
        
    def add_setting(self):
        
        if not self.first_init:
            self.remove_setting()
        
        tempsetting = RoutineData.Setting(RoutineData.Parameter.TEMPERATURE, RoutineData.Temperature(self.temp_value.value()))
        lightsetting = RoutineData.Setting(RoutineData.Parameter.LIGHTMODE, RoutineData.Light(self.lightmodes[self.light_modes_box.currentText()]))
        self.routine.add_setting_to_slot(self.slot.uid, tempsetting)
        self.routine.add_setting_to_slot(self.slot.uid, lightsetting)
        
    def remove_setting(self):

        self.routine.delete_setting_from_slot(self.slot.uid, RoutineData.Parameter.TEMPERATURE)
        self.routine.delete_setting_from_slot(self.slot.uid, RoutineData.Parameter.LIGHTMODE)