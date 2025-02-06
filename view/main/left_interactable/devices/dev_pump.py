from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

from operator_mod.logger.global_logger import Logger
from controller.device_handler.devices.pump_device.pump import Pump
from operator_mod.in_mem_storage.in_memory_data import InMemoryData

class SetWaiter(QThread):
    
    pass

class UIPumpWidget(QWidget):
    
    def __init__(self):
        
        super().__init__()
        
        self.data = InMemoryData()
        self.pump = Pump.get_instance()
        self.logger = Logger("Application").logger
    
    def setupForm(self):
        
        # Main layout that is set to self
        self.mainlayout = QVBoxLayout()
        
        # The top layout with current fill level, syringe params and more
        self.info_widget = QWidget()
        self.info_layout = QFormLayout()
        
        self.fill_level_label = QLabel()
        
        # Adjustable syringe parameters
        self.syringe_diameter_label = QDoubleSpinBox()
        self.syringe_diameter_label.setRange(0, 1000)
        self.syringe_diameter_label.setSingleStep(0.01)
        self.syringe_diameter_label.editingFinished.connect(self._syringe_params_changed)
        
        self.syringe_length_label = QDoubleSpinBox()
        self.syringe_length_label.setRange(0, 1000)
        self.syringe_length_label.setSingleStep(0.01)
        self.syringe_length_label.editingFinished.connect(self._syringe_params_changed)
        
        self._update_info_labels()
        
        self.info_layout.addRow("Fill level: ", self.fill_level_label)
        self.info_layout.addRow("Syringe Diameter: ", self.syringe_diameter_label)
        self.info_layout.addRow("Syringe Length: ", self.syringe_length_label)
        
        self.info_widget.setLayout(self.info_layout)
        
        self.mainlayout.addWidget(self.info_widget)
        
        # TabLayout
        self.maintabwidget = QTabWidget()
        
        ### Load Layout
        self.load_widget = QWidget()
        self.load_layout = QVBoxLayout()
        self.volume_layout = QHBoxLayout()
        
        self.volume_load_label = QLabel("Volume")
        self.volume_load = QSpinBox()
        self.volume_load.setRange(0, 2500)
        
        self.volume_load_unit = QLabel("μL")
        
        self.volume_layout.addWidget(self.volume_load_label)
        self.volume_layout.addWidget(self.volume_load)
        self.volume_layout.addWidget(self.volume_load_unit)
        
        self.load_button = QPushButton("Aspirate")
        self.load_button.clicked.connect(self.load_button_action)
        
        self.load_layout.addLayout(self.volume_layout)
        self.load_layout.addWidget(self.load_button)
        
        self.load_widget.setLayout(self.load_layout)
        
        ### Unload Fluid Layout
        self.unload_widget = QWidget()
        self.unload_layout = QVBoxLayout()
        
        self.unload_info_layoutwrapper = QVBoxLayout()
        self.unload_volume_layout = QHBoxLayout()
        self.unload_flowrate_layout = QHBoxLayout()
        
        self.volume_unload_label = QLabel("Volume")
        self.volume_unload = QSpinBox()
        self.volume_unload.setRange(1, 2500)
        self.volume_unload_unit = QLabel("μL")
        
        self.flowrate_label = QLabel("Flowrate")
        self.flowrate_unload = QSpinBox()
        self.flowrate_unload.setRange(1, 1000)
        self.flowrate_unit = QLabel("μL/s")
        
        self.unload_volume_layout.addWidget(self.volume_unload_label)
        self.unload_volume_layout.addWidget(self.volume_unload)
        self.unload_volume_layout.addWidget(self.volume_unload_unit)
        
        self.unload_flowrate_layout.addWidget(self.flowrate_label)
        self.unload_flowrate_layout.addWidget(self.flowrate_unload)
        self.unload_flowrate_layout.addWidget(self.flowrate_unit)
        
        self.unload_info_layoutwrapper.addLayout(self.unload_volume_layout)
        self.unload_info_layoutwrapper.addLayout(self.unload_flowrate_layout)
        
        self.unload_button = QPushButton("Dispense")
        self.unload_button.clicked.connect(self.unload_button_action)
        
        self.unload_info_layoutwrapper.addWidget(self.unload_button)
        
        self.unload_layout.addLayout(self.unload_info_layoutwrapper)
        self.unload_widget.setLayout(self.unload_layout)
        
        ### Main setter
        self.maintabwidget.addTab(self.load_widget, "Aspirate Fluid")
        self.maintabwidget.addTab(self.unload_widget, "Dispense Fluid")
        self.mainlayout.addWidget(self.maintabwidget)
        
        self.setLayout(self.mainlayout)
    
    def load_button_action(self):
        
        load_volume = self.volume_load.value()
        
        self.data.add_data(self.data.Keys.PUMP_LOAD_VOLUME, load_volume, self.data.Namespaces.PUMP)
        self.pump.add_task(self.pump.States.LOAD_FLUID, 0)

    def unload_button_action(self):
        
        unload_volume = self.volume_unload.value()
        unload_flowrate = self.flowrate_unload.value()
        
        self.data.add_data(self.data.Keys.PUMP_UNLOAD_VOLUME, unload_volume, self.data.Namespaces.PUMP)
        self.data.add_data(self.data.Keys.PUMP_FLOW, unload_flowrate, self.data.Namespaces.PUMP)
        self.pump.add_task(self.pump.States.UNLOAD_FLUID, 0)
    
    def _update_info_labels(self):
        
        fill = self.pump.fill_level
        diameter, stroke = self.pump.syringe_params
        
        # Blocking signals for updating the label
        self.syringe_diameter_label.blockSignals(True)
        self.syringe_length_label.blockSignals(True)
        
        self.fill_level_label.setText(str(fill))
        self.syringe_diameter_label.setValue(float(diameter))
        self.syringe_length_label.setValue(float(stroke))
        
        self.syringe_diameter_label.blockSignals(False)
        self.syringe_length_label.blockSignals(False)
        
    def _syringe_params_changed(self):
        
        diameter = self.syringe_diameter_label.value()
        length = self.syringe_length_label.value()
        
        self.data.add_data(self.data.Keys.SYRINGE_DIAMETER, diameter, self.data.Namespaces.PUMP)
        self.data.add_data(self.data.Keys.SYRINGE_LENGTH, length, self.data.Namespaces.PUMP)
        
        self.pump.add_task(self.pump.States.SYRINGE_SETTER, 0)
        
        self._update_info_labels()
        
    def closeEvent(self, event: QCloseEvent):
        
        try:
            if self.timer.isActive():
                self.timer.stop()
                
            from view.main.mainframe import MainWindow
            inst = MainWindow.get_instance()
            subwindows = inst.middle_layout.mdi_area.subWindowList()

            for subwindow in subwindows:
                if isinstance(subwindow.widget(), UIPumpWidget):
                    inst.middle_layout.mdi_area.removeSubWindow(subwindow)

        except Exception as e:
            self.logger.warning(f"Unclean subwindow exit in UI MFCWidget: {e}")
        
        finally:
            event.accept()