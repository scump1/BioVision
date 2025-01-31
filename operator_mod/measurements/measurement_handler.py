
import time
from PySide6.QtWidgets import QMessageBox

from model.measurements.measurement_creator import MeasurementCreator
from operator_mod.measurements.measurement_runner.measurement_runner import MeasurementRunner
from view.liveviewForm.liveview_form import LiveViewForm

from model.measurements.routine_system.routine_system import RoutineSystem

class MeasurementHandler:
    """Handles the creation and setup of a measurement. Creates the measurement folder, and every folder for a slot in the routine with calibration and result folder. Starts the Measurement Runner. 
    """
    
    def __init__(self) -> None:
        
        self.creator = MeasurementCreator()
        self.routinesystem = None
    
    def setup_measurement(self, name: str, routinesystem: RoutineSystem) -> None:
        """Sets up the directory structure for a routine. Creates several directories and configures result SQL data tables.

        Args:
            name (str): The Routine name from the form.
            routinesystem (RoutineSystem): The associated DataSystem
        """

        self.routinesystem = routinesystem
        
        # Creating the Measurement Folder and the Slot Structure with results and stuff for each slot based on the RoutineSystem
        # All slots and their folders are now in the ResourceManager available under the slots name, which is accessible everywhere where the RoutineSystem is
        self.creator.create_dir(name, routinesystem)
    
    def start_measurement(self) -> None:

        # Starts the measurement interface
        from view.main.mainframe import MainWindow
            
        instance = MainWindow.get_instance()
        
        if self.routinesystem is None:
            QMessageBox.warning(instance, "Error", "Could not create the appropiate folder structures. Consult Leon.", QMessageBox.StandardButton.Close)
            return
        
        mdi_area = instance.middle_layout.mdi_area
        subwindows = mdi_area.subWindowList()
        
        for subwindow in subwindows:

            if isinstance(subwindow.widget(), LiveViewForm):
                subwindow.close()
        
        time.sleep(1)
        
        ## Here we start the Runner with the information
        self.runner = MeasurementRunner(self.routinesystem)
        self.runner.start()
    
    def stop_measurement(self):
        
        if self.runner.is_alive():
            self.runner.stop_flag.set()
    
        self.runner.shutdown()
        del self.runner
    
    def time_calc(self, time: float, unit: str, target: str = 's') -> float:
        """Calculates a runtime in a target time value given parameters.

        Args:
            value (float): The time value.
            unit (str): The time unit. ['s', 'min', 'h']
            target (str, optional): The target time unit. Defaults to 's'. ['s', 'min', 'h']

        Returns:
            float: The converted time value in the target unit.
        """
                
        if unit == target:
            return time

        if time <= 0:
            return 0

        # Conversion factors for time units
        conversion_factors = {
            's': {'min': 1/60, 'h': 1/3600},
            'min': {'s': 60, 'h': 1/60},
            'h': {'s': 3600, 'min': 60}
        }

        if unit not in conversion_factors or target not in conversion_factors[unit]:
            raise ValueError(f"Invalid time units: {unit} to {target}")

        return int(time * conversion_factors[unit][target])