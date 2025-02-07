
from PySide6.QtWidgets import *

from model.measurements.routine_system.routine_system import RoutineData

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
        
        wrapper_layout = QVBoxLayout()
        tab_widget = QTabWidget()
        
        ## For the Mass Flow
        mf_widget = QWidget()
        mf_layout = QHBoxLayout()
        
        name = QLabel("MFC")
        mf_layout.addWidget(name)
        
        # The setting
        mfc_layout = QVBoxLayout()
        mfclabel = QLabel("Mass Flow")
        
        mfc_unit = QComboBox()
        mfc_unit.addItems(["mL/min"])
        
        self.mfc_value = QDoubleSpinBox()
        self.mfc_value.setValue(5.0)
        self.mfc_value.setSingleStep(0.01)
        self.mfc_value.setRange(0, 70)
        self.mfc_value.valueChanged.connect(self.add_setting)
        
        mfc_layout.addWidget(mfclabel)
        mfc_layout.addWidget(mfc_unit)
        mfc_layout.addWidget(self.mfc_value)
        
        mf_layout.addLayout(mfc_layout)
        mf_widget.setLayout(mf_layout)
        
        tab_widget.addTab(mf_widget, "Massflow")
        
        ### For advanced settings
        advanced_widget = QWidget()
        advanced_layout = QHBoxLayout()
        
        self.mf_interrupt_checkbox = QCheckBox("Turn off massflow during image capture")
        self.mf_interrupt_checkbox.setChecked(False)
        self.mf_interrupt_checkbox.stateChanged.connect(self.add_setting)
        
        advanced_layout.addWidget(self.mf_interrupt_checkbox)
        advanced_widget.setLayout(advanced_layout)
        
        tab_widget.addTab(advanced_widget, "Advanced")
        
        # Wrapping
        wrapper_layout.addWidget(tab_widget)
        self.setLayout(wrapper_layout)
                
    def add_setting(self):
        
        if not self.first_init:
            self.remove_setting()
        
        setting = RoutineData.Setting(RoutineData.Parameter.MFC, RoutineData.MaFlCo(massflow=self.mfc_value.value(), interrupt=self.mf_interrupt_checkbox.isChecked()))
        self.routine.add_setting_to_slot(self.slot.uid, setting)
    
    def remove_setting(self):
        self.routine.delete_setting_from_slot(self.slot.uid, RoutineData.Parameter.MFC)
