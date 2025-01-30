
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QStackedWidget, QSizePolicy, QCheckBox, QPushButton, QToolButton, QMessageBox, QGroupBox
from PySide6.QtCore import Qt

import os

from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from model.utils.SQL.sql_manager import SQLManager

class CalculaionForm(QWidget):
    
    def __init__(self):
        
        super().__init__()
        
        self.data = InMemoryData()
        self.sql = SQLManager()
        
    def setupForm(self):
        
        self.main_wrapper = QHBoxLayout()
        
        ### Calculation Form
        self.calculate_form = QStackedWidget()
        
        # Page 1: Calculations for Bubble Size
        self.bubblesizedist_page = QWidget()
        
        self.bubblesizedist_page_layout = QVBoxLayout()
        self.bubblesizedist_page_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Everything that is dameter related
        self.diamter_gb = QGroupBox("Diameters")
        self.diamter_gb_layout = QVBoxLayout()
        
        self.meanD = QCheckBox("Mean Diameter")
        self.geoD = QCheckBox("Log-Mean Diameter")
        self.sauterD = QCheckBox("Sauter Diameter")
        self.volumetricD = QCheckBox("Volumetric Mean Diameter")
        
        self.diamter_gb_layout.addWidget(self.meanD)        
        self.diamter_gb_layout.addWidget(self.geoD)
        self.diamter_gb_layout.addWidget(self.sauterD)
        self.diamter_gb_layout.addWidget(self.volumetricD)

        self.diamter_gb.setLayout(self.diamter_gb_layout)
        
        self.bubblesizedist_page_layout.addWidget(self.diamter_gb)
        self.bubblesizedist_page.setLayout(self.bubblesizedist_page_layout)
        
        self.calculate_form.addWidget(self.bubblesizedist_page)
        
        ### Rightside interaction layout
        self.rightside_layout_wrapper = QWidget()
        self.rightside_layout_wrapper.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.rightside_layout_wrapper.setMaximumWidth(325)
        self.rightside_layout = QVBoxLayout()
        self.rightside_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.measurement_picker_label = QLabel("Pick a measurement:")

        self.measurement_picker = QComboBox()
        self.measurement_picker.currentTextChanged.connect(lambda: self.parameter_setter(self.measurement_picker.currentText()))

        self.result_picker_label = QLabel("Pick a dataset:")

        self.result_picker = QComboBox()
        
        # Calculate button
        self.calc_button = QPushButton("Calculate")

        self.rightside_layout.addWidget(self.measurement_picker_label)
        self.rightside_layout.addWidget(self.measurement_picker)
        self.rightside_layout.addWidget(self.result_picker_label)
        self.rightside_layout.addWidget(self.result_picker)
        self.rightside_layout.addWidget(self.calc_button)

        self.rightside_layout_wrapper.setLayout(self.rightside_layout)
        
        self.main_wrapper.addWidget(self.calculate_form)
        self.main_wrapper.addWidget(self.rightside_layout_wrapper)
        
        self.setLayout(self.main_wrapper)
        
    def parameter_setter(self, name):

        ### We would get the measurement table result headers here and classify them as parameters
        # possible_tables = ["environment", "BubbleSizeResults"]

        res_folder = os.path.join(self.data.get_data("ProjectFolderResult"), name)
           
        if os.path.exists(res_folder):

            self.mm_data = os.path.join(res_folder, "data.db")
            query = """SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"""

            result = self.sql.read_or_write(self.mm_data, query, "read")

            # Adding the different results as selection to the picker
            self.result_picker.blockSignals(True)
            self.result_picker.clear()
            for item in result:

                if item[0] == "environment":
                    self.result_picker.addItem("Environment")
                    
                elif item[0] == "BubbleSizeResults":
                    self.result_picker.addItem("Bubble Size Analysis")

            self.result_picker.setCurrentText("Environment")
            self.result_picker.blockSignals(False)