
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QPushButton, QProgressBar
from PySide6.QtCore import Qt

class MeasurementGUI(QWidget):
    
    def __init__(self) -> None:
        
        super().__init__()
        
    def setupWidget(self):
        
        mainlayout = QVBoxLayout()
        
        ### Slot layout
        top_layout = QHBoxLayout()
        
        # The layout for the current and next slot
        self.slot_grid = QGridLayout()
        self.slot_grid.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        current = QLabel("Current Slot: ")
        self.current_slot_label = QLabel()
        
        next = QLabel("Started: ")
        self.next_slot_label = QLabel("Now")
        
        self.slot_grid.addWidget(current, 0, 0)
        self.slot_grid.addWidget(self.current_slot_label, 0, 1)
        self.slot_grid.addWidget(next, 1, 0)
        self.slot_grid.addWidget(self.next_slot_label, 1, 1)
        
        # Stop button
        self.stop_button = QPushButton("Stop Measurement")
        self.stop_button.setMaximumWidth(125)
        
        top_layout.addLayout(self.slot_grid)
        top_layout.addWidget(self.stop_button)
        
        mainlayout.addLayout(top_layout)
        
        ### Progress Bar
        
        self.progressbar = QProgressBar()
        
        mainlayout.addWidget(self.progressbar)
        
        self.setLayout(mainlayout)