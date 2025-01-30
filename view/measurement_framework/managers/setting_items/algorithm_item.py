
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox

from model.measurements.routine_system.routine_system import RoutineSystem, RoutineData

class AlgorithmItemWidget(QWidget):
    
    def __init__(self, routinesystem, slot) -> None:
        super().__init__()
        
        self.slot = slot

        self.routine = routinesystem
        
        self.first_init = True
        
        self.setup()
        self.add_setting()      
          
        self.first_init = False
        
    def setup(self):
        
        mainlayout = QHBoxLayout()
        
        name = QLabel("Algorithm")
        
        # Algorithm Picker
        self.algorithms = QComboBox()
        self.algorithms.addItems(["Bubble Size", "Mixing Time"])
        self.algorithms.currentTextChanged.connect(self.add_setting)
        
        mainlayout.addWidget(name)
        mainlayout.addWidget(self.algorithms)
        
        self.setLayout(mainlayout)
        
    def add_setting(self):
        
        if not self.first_init:
            self.remove_setting()
        
        setting = None
        if self.algorithms.currentIndex() == 0:
            setting = RoutineData.Setting(name=RoutineData.Parameter.ALGORITHMS, setting=RoutineData.Algorithm(algorithm=RoutineData.AlgorithmType.BUBBLE_SIZE))
        
        elif self.algorithms.currentIndex() == 1:
            setting = RoutineData.Setting(name=RoutineData.Parameter.ALGORITHMS, setting=RoutineData.Algorithm(algorithm=RoutineData.AlgorithmType.PELLET_SIZE))
       
        if setting is not None: 
            self.routine.add_setting_to_slot(self.slot.uid, setting)
        
    def remove_setting(self):
        
        self.routine.delete_setting_from_slot(self.slot.uid, RoutineData.Parameter.ALGORITHMS)