
from PySide6.QtWidgets import *

from model.measurements.routine_system.routine_system import RoutineData, RoutineSystem

class MFCItemWidget(QWidget):
    
    def __init__(self, routinesystem, slot):
        
        super().__init__()
        
        self.slot = slot

        self.routine = routinesystem
        
        self.first_init = True
        
        self.setupWidget()
        self.add_setting()
        
        self.first_init = False
        
    def setupWidget(self):
        
        mainlaoyut = QHBoxLayout()
        
        name = QLabel("MFC")
        mainlaoyut.addWidget(name)
        
        # The setting
        mfc_layout = QVBoxLayout()
        mfclabel = QLabel("Mass Flow")
        
        mfc_unit = QComboBox()
        mfc_unit.addItems(["mL/min"])
        
        self.mfc_value = QDoubleSpinBox()
        self.mfc_value.setValue(5.0)
        self.mfc_value.setRange(0, 50)
        self.mfc_value.valueChanged.connect(self.add_setting)
        
        mfc_layout.addWidget(mfclabel)
        mfc_layout.addWidget(mfc_unit)
        mfc_layout.addWidget(self.mfc_value)
        
        mainlaoyut.addLayout(mfc_layout)
        
        self.setLayout(mainlaoyut)
        
    def add_setting(self):
        
        if not self.first_init:
            self.remove_setting()
        
        setting = RoutineData.Setting(RoutineData.Parameter.MFC, RoutineData.MaFlCo(massflow=self.mfc_value.value()))
        self.routine.add_setting_to_slot(self.slot.uid, setting)
    
    def remove_setting(self):
        self.routine.delete_setting_from_slot(self.slot.uid, RoutineData.Parameter.MFC)
        