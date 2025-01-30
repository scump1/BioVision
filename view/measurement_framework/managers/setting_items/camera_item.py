
from PySide6.QtWidgets import *

from model.measurements.routine_system.routine_system import RoutineData

class CameraItemWidget(QWidget):
    
    def __init__(self, routinesystem, slot):
        
        super().__init__()
        
        self.slot = slot

        self.routine = routinesystem
        
        self.first_init = True # This just prevents the first delete from happening before anythinG WAS INITILAIZED
        
        self.setupWidget()
        self.add_setting()
        
        self.first_init = False  
    
    def setupWidget(self):
        
        mainlayout = QHBoxLayout()
        
        # Name
        name = QLabel("Camera")
        mainlayout.addWidget(name)
        
        # Images
        img_layout = QVBoxLayout()
        img = QLabel("Images per Execution")
        self.img_count = QSpinBox()
        self.img_count.setMinimum(1)
        self.img_count.setMaximum(32)
        
        self.img_count.valueChanged.connect(self.add_setting)
        
        img_layout.addWidget(img)
        img_layout.addWidget(self.img_count)
        
        # Interval
        interval_layout = QVBoxLayout()
        interval = QLabel("Interval")
        self.interval_count = QDoubleSpinBox()
        self.interval_count.setMinimum(0.001)
        self.interval_count.setMaximum(9999)
        self.interval_count.setValue(5)
        
        self.interval_count.valueChanged.connect(self.add_setting)
        
        self.interval_time_unit = QComboBox()
        self.interval_time_unit.addItems(["s", "min", "h"])
        
        self.interval_time_unit.currentTextChanged.connect(self.add_setting)
        
        interval_layout.addWidget(interval)
        interval_layout.addWidget(self.interval_count)
        interval_layout.addWidget(self.interval_time_unit)
        
        # ToolBox Button that redirects to settings
        tool_button = QPushButton("...")
        tool_button.setFixedSize(30,30)
        
        mainlayout.addLayout(img_layout)
        mainlayout.addLayout(interval_layout)
        mainlayout.addWidget(tool_button)
        
        self.setLayout(mainlayout)
        
    def add_setting(self):
        
        if not self.first_init:
            # First we need to delete the old settings
            self.remove_setting()
        
        # Runtime      
        if 's' == self.interval_time_unit.currentText():
            runtime = self.interval_count.value()
        elif 'min' == self.interval_time_unit.currentText():
            runtime = self.interval_count.value() * 60
        elif 'h' == self.interval_time_unit.currentText():
            runtime = self.interval_count.value() * 3600
        
        # Then we add the new parameter
        setting = RoutineData.Setting(RoutineData.Parameter.CAMERA, RoutineData.Camera(img_count=self.img_count.value(), interval=runtime))
        self.routine.add_setting_to_slot(self.slot.uid, setting)  
        
    def remove_setting(self):
        
        self.routine.delete_setting_from_slot(self.slot.uid, RoutineData.Parameter.CAMERA)