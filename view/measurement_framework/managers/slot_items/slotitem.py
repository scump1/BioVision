import string

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from model.measurements.routine_system.routine_system import RoutineData

class SlotItemWidget(QWidget):
    
    def __init__(self, slot, routinesystem):
        
        super().__init__()
        
        self.slot = slot
        self.routine = routinesystem
        
        # Saving layouts for removal
        self.condition_widget = None
        
        self.setup()

    def setup(self):
        
        mainlayout = QHBoxLayout()
        tabber = QTabWidget()
        
        # Standard Tab
        standard_tab = self._setup_standard_tab()
        
        # condition Tab
        condition_tab = self._setup_condition_widget()
        
        tabber.addTab(standard_tab, "Slot")
        tabber.addTab(condition_tab, "Condition")
        
        mainlayout.addWidget(tabber)
        self.setLayout(mainlayout)
    
    def _setup_standard_tab(self) -> QWidget:
        
        mainwidget = QWidget()
        mainlayout = QHBoxLayout()
        
        # Name
        name_layout = QVBoxLayout()
        name_label = QLabel("Name")
        self.name_edit = QLineEdit()
        self.name_edit.setMaximumWidth(250)
        self.name_edit.textChanged.connect(self.update_slot_property)
        
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)
        
        # Runtime
        runtime_layout = QVBoxLayout()
        runtime_label = QLabel("Runtime")
        
        runtime_set_layout = QVBoxLayout()
        self.runtime_value = QDoubleSpinBox()
        self.runtime_value.setRange(0, 999)
        self.runtime_value.valueChanged.connect(self.update_slot_property)
        
        self.runtime_unit = QComboBox()
        self.runtime_unit.addItems(["s", "min", "h"])
        self.runtime_unit.currentTextChanged.connect(self.update_slot_property)
        
        runtime_set_layout.addWidget(self.runtime_unit)
        runtime_set_layout.addWidget(self.runtime_value)
        
        runtime_layout.addWidget(runtime_label)
        runtime_layout.addLayout(runtime_set_layout)
        
        mainlayout.addLayout(name_layout)
        mainlayout.addLayout(runtime_layout)
        
        mainwidget.setLayout(mainlayout)
        
        return mainwidget
        
    def _setup_condition_widget(self) -> QWidget:
        
        mainwidget = QWidget()
        mainlayoutwrapper = QVBoxLayout()
        mainlayout = QHBoxLayout()
        
        self.condition = QCheckBox("Enable")
        self.condition.setChecked(False)
        self.condition.stateChanged.connect(self.update_slot_property)
        self.condition.stateChanged.connect(self._condition_enabler_disabler)

        self.condition_picker = QComboBox()
        self.condition_picker.addItems(["Temperature", "Pellet Size"])
        self.condition_picker.currentTextChanged.connect(self.update_slot_property)
        
        ### Interaction
        self.stopwait = QCheckBox("Stop and Wait")
        self.stopwait.stateChanged.connect(self.update_slot_property)
        
        self.compare_type = QComboBox()
        self.compare_type.addItems([">", "=", "<"])
        self.compare_type.currentIndexChanged.connect(self.update_slot_property)
        
        self.condition_value = QDoubleSpinBox()
        self.condition_value.setValue(20.0)
        self.condition_value.valueChanged.connect(self.update_slot_property)
        
        mainlayout.addWidget(self.condition)
        mainlayout.addWidget(self.condition_picker)
        mainlayout.addWidget(self.compare_type)
        mainlayout.addWidget(self.condition_value)
        
        mainlayoutwrapper.addLayout(mainlayout)
        mainlayoutwrapper.addWidget(self.stopwait)
        
        mainwidget.setLayout(mainlayoutwrapper)
                   
        self._condition_enabler_disabler() # actually calling it once here
        
        return mainwidget
    
    def _condition_enabler_disabler(self):
        state = self.condition.isChecked()
        self.condition_picker.setEnabled(state)
        self.compare_type.setEnabled(state)
        self.condition_value.setEnabled(state)
                    
    def update_slot_property(self):
        
        # Name
        name = self.name_edit.text()
        name = self.sanitize_project_name(name)
        self.slot.name = name
        
        # Runtime      
        if 's' == self.runtime_unit.currentText():
            runtime = self.runtime_value.value()
        elif 'min' == self.runtime_unit.currentText():
            runtime = self.runtime_value.value() * 60
        elif 'h' == self.runtime_unit.currentText():
            runtime = self.runtime_value.value() * 3600
            
        self.slot.runtime = runtime
        self.slot.interaction = RoutineData.InteractionType.STOP_AND_WAIT if self.stopwait.isChecked() == True else None
        
        if self.condition.isChecked():
            
            param = {
                'Temperature': RoutineData.Parameter.TEMPERATURE,
            }
            
            cond_type = {
                '>': RoutineData.ConditionType.GREATER_THAN,
                '=': RoutineData.ConditionType.EQUAL_TO,
                '<': RoutineData.ConditionType.LESS_THAN
            }
            
            condition = RoutineData.ParameterCondition(parameter=param[self.condition_picker.currentText()], condition_type=cond_type[self.compare_type.currentText()], target_value=self.condition_value.value())
            self.slot.condition = condition 
            
    def sanitize_project_name(self, name: str) -> str:
        """Removes all invalid chars from a name for file/dir creation.

        Args:
            name (str): Any string name.

        Returns:
            str: the sanitized name
        """
        # Define invalid characters: control characters, punctuation, and whitespace
        invalid_chars = set(chr(i) for i in range(0x00, 0x20))  # Control characters
        invalid_chars.update(string.punctuation)  # All punctuation characters
        invalid_chars.add(' ')  # Add whitespace explicitly
        
        # Replace each invalid character with an underscore
        sanitized_name = ''.join(char if char not in invalid_chars else '_' for char in name)
        
        return sanitized_name