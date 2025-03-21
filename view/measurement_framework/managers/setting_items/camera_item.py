
from PySide6.QtWidgets import *
from PySide6.QtCore import Qt

from controller.device_handler.devices.camera_device.camera import Camera
from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from model.measurements.routine_system.routine_system import RoutineData

class CameraItemWidget(QWidget):
    
    def __init__(self, routinesystem, slot):
        
        super().__init__()
        
        self.data = InMemoryData()
        self.camera = Camera.get_instance()
        
        self.slot = slot

        self.routine = routinesystem
        
        self.first_init = True # This just prevents the first delete from happening before anythinG WAS INITILAIZED
        
        self.setupWidget()
        self.add_setting()
        
        self.first_init = False  
    
    def setupWidget(self):
        
        mainlayout = QHBoxLayout()
        
        # Main background widget
        tabwidget = QTabWidget()
        
        # Page one is general settings
        general_widget = QWidget()
        general_layout = QGridLayout()
        general_widget.setLayout(general_layout)
        
        # Name
        name = QLabel("Camera")
        general_layout.addWidget(name, 1, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Images
        img = QLabel("Images per Execution")
        self.img_count = QSpinBox()
        self.img_count.setMinimum(1)
        self.img_count.setMaximum(32)
        
        self.img_count.valueChanged.connect(self.add_setting)
        
        general_layout.addWidget(img, 0, 1)
        general_layout.addWidget(self.img_count, 1, 1)
        
        # Interval
        interval = QLabel("Interval")
        self.interval_count = QDoubleSpinBox()
        self.interval_count.setMinimum(1)
        self.interval_count.setMaximum(999)
        self.interval_count.setValue(1)
        
        self.interval_count.valueChanged.connect(self.add_setting)
        
        self.interval_time_unit = QComboBox()
        self.interval_time_unit.addItems(["s", "min", "h"])
        
        self.interval_time_unit.currentTextChanged.connect(self.add_setting)
        
        general_layout.addWidget(interval, 0, 2)
        general_layout.addWidget(self.interval_count, 1, 2)
        general_layout.addWidget(self.interval_time_unit, 2, 2)
        
        # Tabwidget adding
        tabwidget.addTab(general_widget, "Image capture")
        
        # Page two is Area of Interest
        roi_page = QWidget()
        roi_layout = QGridLayout()
        roi_page.setLayout(roi_layout)
        
        roi_label = QLabel("Area of interest")
        roi_layout.addWidget(roi_label, 1, 0)
        
        self.roi_picker = QComboBox()
        self.roi_picker.addItems(["All", "Column", "Column with Top"])
        self.roi_picker.currentTextChanged.connect(self._roi_pick_changed)
        
        roi_layout.addWidget(self.roi_picker, 1, 1)
        
        tabwidget.addTab(roi_page, "Area of interest")
        
        # Mainlayout
        
        mainlayout.addWidget(tabwidget)
        
        self.setLayout(mainlayout)
    
    def _roi_pick_changed(self):
        
        if self.roi_picker.currentText() == "All":
            self.data.add_data(self.data.Keys.AREA_OF_INTERST, self.camera.AreaOfInterest.ALL, self.data.Namespaces.CAMERA)
            
        elif self.roi_picker.currentText() == "Column":
            self.data.add_data(self.data.Keys.AREA_OF_INTERST, self.camera.AreaOfInterest.COLUMN, self.data.Namespaces.CAMERA)
            
        elif self.roi_picker.currentText() == "Column with Top":
            self.data.add_data(self.data.Keys.AREA_OF_INTERST, self.camera.AreaOfInterest.COLUMN_WITH_TOP, self.data.Namespaces.CAMERA)
     
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