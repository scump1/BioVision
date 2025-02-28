
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

import uuid

from view.single_image_analysis.bubble_size_widget.bubble_size_widget import BubbleSizeWidget
from view.single_image_analysis.pellet_size_widget.pellet_size_widget import PelletSizeWidghet

from controller.algorithms.algorithm_manager_class.algorithm_manager import AlgorithmManager
from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from operator_mod.eventbus.event_handler import EventManager
from operator_mod.logger.global_logger import Logger

class SingleImageAnylsisForm(QStackedWidget):

    """This is the holder of several subforms for different algorithms to be used in a single shot mode. They are stacked in a QStackedWidget. Each page is dedicated to a single
    algorithm and its results. Every page consists of three tabs: Setup (The inpout) and visualization and result tabs. 
    """

    def __init__(self):
        
        super().__init__()
        
        self.data = InMemoryData()
        self.events = EventManager.get_instance()
    
        self.events.add_listener(self.events.EventKeys.SI_FORM_BACK_BUTTON, self._back_button_action, 0, True)
        
        self.algman = AlgorithmManager.get_instance()
        
        self.logger = Logger("Application").logger
        self.uid = uuid.uuid4()
        
    def setupForm(self) -> QWidget:
        
        self.setMinimumSize(QSize(1000, 600))
        
        ### This is the first page aka welcome and algorithm select
        # The main layout that holds the gridlayout
        mainwidget = QWidget()
        mainlayout = QVBoxLayout()
        mainlayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # An information label
        infolabel = QLabel("Welcome to the Image Analysis Tool! This application allows you to select from a variety of advanced image analysis algorithms to process your chosen images. Simply pick an algorithm, analyze your images, and explore the results. You can also save your analysis outputs for future use. Get started now and unlock powerful insights from your images! ")
        infolabel.setWordWrap(True)
        mainlayout.addWidget(infolabel)
        
        # Seperator
        sep = QSpacerItem(10, 10, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        mainlayout.addItem(sep)
        
        ### The options and shit
        algorithm_layout = QHBoxLayout()
        # Now some options
        alg_label = QLabel("Algorithm: ")
        algorithm_picker = QComboBox()
        algorithm_picker.addItems(["Bubble Size", "Pellet Size - Microscope Images", "Pellet Size - BioVision"])

        # Continue Buttin
        continuebutton = QPushButton("Continue")
        continuebutton.clicked.connect(lambda: self._continue_button_action(algorithm_picker.currentText()))

        algorithm_layout.addWidget(alg_label)
        algorithm_layout.addWidget(algorithm_picker)
        algorithm_layout.addWidget(continuebutton)

        mainlayout.addLayout(algorithm_layout)
        
        mainwidget.setLayout(mainlayout)
        
        self.addWidget(mainwidget)
        
        ### This is the page for bubble sizing
        bubblesizer = BubbleSizeWidget()
        bubblesizer.setupForm()
        
        self.addWidget(bubblesizer)
        
        ### This is for Pellet Size - Zeiss Microscope
        pelletwidget = PelletSizeWidghet()
        pelletwidget.setupForm()
        
        self.addWidget(pelletwidget)
        
        return self

    def _continue_button_action(self, name: str):
        
        if name == 'Bubble Size':
            self.setCurrentIndex(1)
            
        elif name == "Pellet Size - Microscope Images":
            self.setCurrentIndex(2)

    def _back_button_action(self):
        
        self.setCurrentIndex(0)

    def closeEvent(self, event: QCloseEvent):
        
        try:
            from view.main.mainframe import MainWindow
            
            inst = MainWindow.get_instance()
            
            subwindows = inst.middle_layout.mdi_area.subWindowList()
            
            for subwindow in subwindows:
                widget = subwindow.widget()
                if isinstance(widget, SingleImageAnylsisForm):
                    if self.uid == widget.uid:
                        
                        inst.middle_layout.mdi_area.removeSubWindow(subwindow)
                        
            self.logger.info("Succesfully closed SingleImage Analysis Form.")
            
        except Exception as e:
            self.logger.warning(f"Error in close Event for {self}: {e}.")
            
        finally:
            event.accept()