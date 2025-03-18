
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QTabWidget

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
        
        maintabwidget = QTabWidget()
        
        # Page one
        algorithmwidget = QWidget()
        algorithmlayout = QVBoxLayout()

        # Information label
        information = QLabel("Please ensure the adequate Camera Are of Interest ist selected for proper results.")

        # Algorithm Picker
        self.algorithms = QComboBox()
        self.algorithms.addItems(["Bubble Size", "Mixing Time"])
        self.algorithms.currentTextChanged.connect(self.add_setting)
        
        algorithmlayout.addWidget(information)
        algorithmlayout.addWidget(self.algorithms)
        algorithmwidget.setLayout(algorithmlayout)
        
        maintabwidget.addTab(algorithmwidget, "Algorithm")
        
        mainlayout.addWidget(maintabwidget)
        
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