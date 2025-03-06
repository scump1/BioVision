
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

from operator_mod.logger.global_logger import Logger
from controller.device_handler.devices.pump_device.pump import Pump
from operator_mod.in_mem_storage.in_memory_data import InMemoryData

class UIPumpWidget(QWidget):
    
    def __init__(self):
        
        super().__init__()
        
        self.data = InMemoryData()
        self.pump = Pump.get_instance()
        self.logger = Logger("Application").logger
    
    def setupForm(self):
        
        self.setMinimumSize(QSize(500, 150))
        
        # Main layout that is set to self
        self.mainlayout = QVBoxLayout()
        
        # The top layout with current fill level, syringe params and more
        self.info_widget = QWidget()
        self.info_layout = QFormLayout()
        
        self.fill_level_label = QLabel()
        
        # Adjustable syringe parameters
        self.syringe_diameter_label = QLabel()
        self.syringe_length_label = QLabel()
        
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
        
        self.stop_load_button = QPushButton("Stop")
        self.stop_load_button.clicked.connect(self._stop_pump)
        
        self.load_layout.addLayout(self.volume_layout)
        self.load_layout.addWidget(self.load_button)
        self.load_layout.addWidget(self.stop_load_button)
        
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
        self.flowrate_unload = QDoubleSpinBox()
        self.flowrate_unload.setDecimals(6)
        self.flowrate_unload.setRange(0, 200)
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
        
        self.stop_unload_button = QPushButton("Stop")
        self.stop_unload_button.clicked.connect(self._stop_pump)
        
        self.unload_info_layoutwrapper.addWidget(self.unload_button)
        self.unload_info_layoutwrapper.addWidget(self.stop_unload_button)
        
        self.unload_layout.addLayout(self.unload_info_layoutwrapper)
        self.unload_widget.setLayout(self.unload_layout)
        
        ### Syringe setter layout
        self.syringe_widget = QWidget()
        self.syringe_layout = QGridLayout()
        
        # Label, Spinbox, Unit
        diameter_label = QLabel("Diameter")
        length_label = QLabel("Length")
        
        self.syringe_diameter_spinbox = QDoubleSpinBox()
        self.syringe_diameter_spinbox.setSingleStep(0.01)
        self.syringe_diameter_spinbox.setRange(0, 25)
        self.syringe_diameter_spinbox.editingFinished.connect(self._syringe_params_changed)
        
        self.syringe_length_spinbox = QSpinBox()
        self.syringe_length_spinbox.setSingleStep(1)
        self.syringe_length_spinbox.setRange(50, 60)
        self.syringe_length_spinbox.editingFinished.connect(self._syringe_params_changed)
        
        self._set_inital_syringe_params()
        
        mm_diameter_unit_label = QLabel("mm")
        mm_length_unit_label = QLabel("mm")
        
        self.syringe_layout.addWidget(diameter_label, 0, 0)
        self.syringe_layout.addWidget(self.syringe_diameter_spinbox, 0, 1)
        self.syringe_layout.addWidget(mm_diameter_unit_label, 0, 2)
        
        self.syringe_layout.addWidget(length_label, 1, 0)
        self.syringe_layout.addWidget(self.syringe_length_spinbox, 1, 1)
        self.syringe_layout.addWidget(mm_length_unit_label, 1, 2)
        
        self.syringe_widget.setLayout(self.syringe_layout)
        
        ### Calibration
        self.calibration_widget = QWidget()
        self.calibration_layout = QVBoxLayout()
        
        self.calibration_button = QPushButton("Calibration")
        self.calibration_button.pressed.connect(self.calibration_button_action)
        
        self.calibration_layout.addWidget(self.calibration_button)
        self.calibration_widget.setLayout(self.calibration_layout)
                
        ### Main setter
        self.maintabwidget.addTab(self.load_widget, "Aspirate Fluid")
        self.maintabwidget.addTab(self.unload_widget, "Dispense Fluid")
        self.maintabwidget.addTab(self.syringe_widget, "Syringe Parameters")
        self.maintabwidget.addTab(self.calibration_widget, "Calibration")
        
        self.mainlayout.addWidget(self.maintabwidget)
        
        self.setLayout(self.mainlayout)
    
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_info_labels)
        self.timer.start(500)
            
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

        # shorten the floats
        self.fill_level_label.setText(f"{fill:.2f}")
        self.syringe_diameter_label.setText(f"{diameter:.2f}")
        self.syringe_length_label.setText(f"{stroke:.2f}")

    def _syringe_params_changed(self):
        
        diameter = float(self.syringe_diameter_spinbox.value())
        length = float(self.syringe_length_spinbox.value())
        
        self.data.add_data(self.data.Keys.SYRINGE_DIAMETER, diameter, self.data.Namespaces.PUMP)
        self.data.add_data(self.data.Keys.SYRINGE_LENGTH, length, self.data.Namespaces.PUMP)
        
        self.pump.add_task(self.pump.States.SYRINGE_SETTER, 0)
    
    def _set_inital_syringe_params(self):
        
        diameter = self.syringe_diameter_label.text()
        length = self.syringe_length_label.text()
        
        self.syringe_diameter_spinbox.setValue(float(diameter))
        self.syringe_length_spinbox.setValue(float(length))
    
    def _stop_pump(self):
        
        self.pump.stop_pump()
        
        self._button_enabler(False)

        timer = QTimer()
        timer.singleShot(10000, lambda: self._button_enabler(True))
        timer.start()
            
    def _button_enabler(self, state: bool):
        
        if state is not None:
            self.load_button.setEnabled(state)
            self.unload_button.setEnabled(state)
    
    def calibration_button_action(self) -> None:
        
        # Warning
        from view.main.mainframe import MainWindow
        instance = MainWindow.get_instance()
        
        result = QMessageBox.warning(instance, "Calibration", "Please ensure the pump platform is viable for calibration, else damage to the device or syringe might be caused. Do you want to continue?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        
        if result == QMessageBox.StandardButton.No:
            return
        
        self.pump.add_task(self.pump.States.CALIBRATE, 0)
    
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