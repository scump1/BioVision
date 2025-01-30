
import datetime

from uuid import uuid4
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from operator_mod.eventbus.event_handler import EventManager
from operator_mod.logger.progress_logger import ProgressLogger
from view.measurement_framework.widgets.profile_widget import ProfileWidget

from view.measurement_framework.managers.setting_manager import SettingsManager
from view.measurement_framework.managers.slot_manager import SlotManager

from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from operator_mod.logger.global_logger import Logger
from operator_mod.measurements.measurement_handler import MeasurementHandler
from model.measurements.routine_system.routine_system import RoutineSystem

class MeasurementFramework(QWidget):
    
    measurement_start = Signal(str)
    measurement_ended_signal = Signal()
    
    stopwait_signal = Signal()
    
    def __init__(self) -> None:
        
        super().__init__()
        
        self.data = InMemoryData()
        self.data.add_data(self.data.Keys.MEASUREMENT_STOPPED_AND_WAITING, False, self.data.Namespaces.MEASUREMENT)
        
        self.events = EventManager()
        self.events.add_listener(self.events.EventKeys.PROFILE_SETTER, self.profile_setter, 0, True)
        self.events.add_listener(self.events.EventKeys.MS_PROGRESS_SLOT, self.set_current_progress_slot, 0, True)
        
        # Stopwait Flag waiting
        self.events.add_listener(self.events.EventKeys.MS_STOPPED_FOR_WAITING, self.stop_and_wait_event, 0, True)
        
        self.events.add_listener(self.events.EventKeys.MS_ENDED, self.measurement_ended, 0, True)
        
        self.logger = Logger("Application").logger
        
        self.uid = uuid4()
        self.routinesystem = RoutineSystem(self.uid)
        
        self.m_handler = MeasurementHandler()
    
        self.timer = None
        
        self.measurement_start.connect(self._start_update)
        self.measurement_ended_signal.connect(self._measurement_ended)
        self.stopwait_signal.connect(self._stop_and_wait_event)
    
    ### GUI Interface setup
    def setupFramework(self):
        
        ## We have two layers: Top and bottom. Top holds a stacked widget with : Page 1 -> Input information and start. Page 2 -> Progress and Stop.
        ## Bottom layer: TabWidget with : Tab 1 -> Slot & Settings and Tba 2 -> Profile Tab

        mainlayout = QVBoxLayout()
        mainlayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Inside the mainlayout we have two Widgets
        
        # Top: StackedWidget
        self.stacked_widget = self._setup_top_widget()
        self.stacked_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        
        # Bottom: TabWidget
        self.tab_widget = self._setup_bottom_widget()
        self.tab_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        mainlayout.addWidget(self.stacked_widget)
        mainlayout.addWidget(self.tab_widget)
        
        # Stretch Factor
        mainlayout.setStretchFactor(self.stacked_widget, 0)
        mainlayout.setStretchFactor(self.tab_widget, 1)
        
        self.setLayout(mainlayout)

    def _setup_bottom_widget(self) -> QTabWidget:
        
        tab_widget = QTabWidget()
        
        # the first page is the slot & settings
        first_page_widget = QWidget()
        first_page_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        first_page_layout = QHBoxLayout()
        
        # Slots
        # The Slot thingy
        self.slot = SlotManager(self.routinesystem)
        self.slot.setupWidget()
        self.slot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Settings
        self.settings = SettingsManager(self.routinesystem)
        self.settings.setupWidget()
        self.settings.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        first_page_layout.addWidget(self.slot)
        first_page_layout.addWidget(self.settings)
        
        first_page_widget.setLayout(first_page_layout)
        
        # The second page is fairly simple
        # Now the profile box     
        self.profile = ProfileWidget(self.routinesystem)
        self.profile.setupWidget()
        self.profile.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Adding together
        tab_widget.addTab(first_page_widget, "Routine Configuration")
        tab_widget.addTab(self.profile, "Profiles")
        
        return tab_widget
        
    def _setup_top_widget(self) -> QStackedWidget:
        
        # The top part
        stacked = QStackedWidget()
        
        input_widget = self._top_input_widget()
        
        progress_widget = self._top_progress_widget()
        
        stacked.addWidget(input_widget)
        stacked.addWidget(progress_widget)
        
        return stacked     
        
    def _top_input_widget(self) -> QWidget:
        
        # Inside we have two widgets: The inpout form and the start button
        input_widget = QWidget()
        input_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        
        input_layout = QHBoxLayout()
        input_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # The input form layout
        input_form = QFormLayout()
        
        # Routine name
        self.routine_name = QLineEdit()
        input_form.addRow("Routine Name: ", self.routine_name)
        
        # Author - we currently do not use this
        input_form.addRow('Author: ', QLineEdit())
        
        # Date
        date = QDateEdit()
        date.setDate(QDate(datetime.date.today()))
        
        input_form.addRow('Date: ', date)
        
        # The start button
        # Start Button in RoutineLayout
        start_button = QPushButton()
        start_button.setIcon(QIcon(r"view\measurement_framework\resources\play-buttton.png"))
        start_button.setFixedSize(50, 50)
        start_button.pressed.connect(self.start_measurement)
        
        ## Adding all of this together
        input_layout.addLayout(input_form)
        input_layout.addWidget(start_button)
        
        input_widget.setLayout(input_layout)
        
        return input_widget
        
    def _top_progress_widget(self) -> QWidget:
    
        # Inside we have the progress form and the stop button
        progress_widget = QWidget()
        progress_widget.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        
        progress_layout = QHBoxLayout()
        progress_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # The progress from
        progress_form = QFormLayout()
        
        self.routine_name_label = QLabel("None", progress_widget)
        progress_form.addRow("Routine Name: ", self.routine_name_label)
        
        self.current_slot = QLabel("None", progress_widget)
        progress_form.addRow("Current Slot: ", self.current_slot)
        
        self.progressbar = QProgressBar()
        progress_form.addRow('Progress: ', self.progressbar)
        
        # The stop button
        stop_button = QPushButton()
        stop_button.setIcon(QIcon(r"view\measurement_framework\resources\stop.png"))
        stop_button.setFixedSize(50, 50)
        stop_button.pressed.connect(self.stop_measurement)
        
        progress_layout.addLayout(progress_form)
        progress_layout.addWidget(stop_button)
        
        progress_widget.setLayout(progress_layout)
        
        return progress_widget
    
    ### Reloading Profiles
    def profile_setter(self, data: list):
        """Sets a profile to the MeasurementFramework environment.

        Args:
            data (list): Unserialized pickle from ProfileManager.
        """
        try:
            if data:
                # First we clear the current slots and settings; This function does both in one
                self.slot.clear_all_slots()
                self.settings.wipe_all_lists()
            
            for slot in data:
                
                runtime, unit = self.runtime_converter(slot.runtime)
                
                slotdata = [slot.name, runtime, unit, slot.condition, slot.interaction]
                self.slot.slot_setter(slotdata)
                                        
                for setting in slot.settings:
                    self.settings.settings_setter(setting)
                
        except Exception as e:
            self.logger.warning(f"Error in setting profile to MeasurementFramework: {e}")
    
    def runtime_converter(self, slottime):
        """Converts the runtime in seconds into a sensible unit format"""
        if slottime > 3600:
            runtime = slottime / 3600
            unit = 'h'
        elif slottime > 60:
            runtime = slottime / 60
            unit = 'min'
        else:
            runtime = slottime
            unit = 's'
            
        return runtime, unit

    ### The events to start and stop
    def start_measurement(self):
        
        from view.main.mainframe import MainWindow
        instance = MainWindow.get_instance()
        
        name = self.routine_name.text()
        
        if not name:
            QMessageBox.information(instance, "Routine Name", "Please enter a valid routine name.", QMessageBox.StandardButton.Ok)
            return 
        
        result = QMessageBox.question(instance, "Start Routine", "Do you really want to start the current routine?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        
        if not result == QMessageBox.StandardButton.Yes:
            return
        
        self.routine_name_label.setText(name)
        self.stacked_widget.setCurrentIndex(1)

        self.tab_widget.setEnabled(False)

        self.m_handler.setup_measurement(name, self.routinesystem)
        self.m_handler.start_measurement()
        
    def stop_measurement(self):
        
        from view.main.mainframe import MainWindow
        
        reply = QMessageBox.warning(MainWindow.get_instance(), "Terminating Routine", "Do you really want to end the current routine?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        
        if not reply == QMessageBox.StandardButton.Yes:
            return
            
        self.m_handler.stop_measurement()    
        
        self.stacked_widget.setCurrentIndex(0)
        self.tab_widget.setEnabled(True)

    ### The events to manage the measurement
    def set_current_progress_slot(self, routinename: str, slotname: str):
        """Sets the current Slot as the Progressloggers reader.

        Args:
            routinename (str): The Routine name to grab the correct Progresslogger
            slotname (str): The current slot name for the scorespace
        """
        
        if self.timer is not None:
            if self.timer.isActive():
                self.timer.stop()
        
        self.current_slot.setText(slotname)
        self.progress_logger = ProgressLogger(routinename) # we are grabbing the current progress log    

        self.measurement_start.emit(slotname)

    def _update_progressbar(self, slotname: str):
        
        if not self.progress_logger:
            return
        
        _, target, current = self.progress_logger.get_progress(slotname)
        
        value = (current / target) * 100
        self.progressbar.setValue(value)
        
    def _start_update(self, name: str):
          
        if self.timer is None:
            self.timer = QTimer()
                    
        self.timer.timeout.connect(lambda: self._update_progressbar(name))

        if not self.timer.isActive():
            self.timer.start(1000)

    def measurement_ended(self):

        self.measurement_ended_signal.emit()
    
    def _measurement_ended(self):
                
        if self.timer is not None:
            self.timer.stop()
            self.timer = None
            
        from view.main.mainframe import MainWindow
        
        QMessageBox.information(MainWindow.get_instance(), "Measurement ended successfully", "Measurement ended succesfully.", QMessageBox.StandardButton.Ok)
        
        self.stacked_widget.setCurrentIndex(0)
        self.tab_widget.setEnabled(True)

    def stop_and_wait_event(self):
        
        self.stopwait_signal.emit()

    def _stop_and_wait_event(self):
        
        from view.main.mainframe import MainWindow
        
        QMessageBox.information(MainWindow.get_instance(), "Waiting for response", "The slot reached its stop and wait condition. Click ok tom continue.", QMessageBox.StandardButton.Ok)
        
        self.data.add_data(self.data.Keys.MEASUREMENT_STOPPED_AND_WAITING, True, self.data.Namespaces.MEASUREMENT)
        
    ### Close Event
    def closeEvent(self, event: QCloseEvent):
        
        try:
            
            if self.timer is not None:
                if self.timer.isActive():
                    self.timer.stop()
            
            from view.main.mainframe import MainWindow
            instance = MainWindow.get_instance()
            
            subwindows = instance.middle_layout.mdi_area.subWindowList()
            
            for subwindow in subwindows:
                widget = subwindow.widget()
                if isinstance(widget, MeasurementFramework):
                    instance.middle_layout.mdi_area.removeSubWindow(subwindow)

        except Exception as e:
            self.logger.info(f"Error in closing MeasurementFramework: {e}.")
            
        finally:
            event.accept()