
import datetime
import os
import re
import string

from operator_mod.logger.global_logger import Logger
from .routine_system.routine_system import RoutineSystem
from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from model.utils.SQL.sql_manager import SQLManager
from model.utils.resource_manager import ResourceManager

class MeasurementCreator:
    
    def __init__(self):
        
        self.logger = Logger("Application").logger
        self.data = InMemoryData()
        self.sql = SQLManager()
        self.resman = ResourceManager()
    
    def create_dir(self, name: str, routinesystem: RoutineSystem) -> list:
        """Creates the topmost Routine Directory where all Slots are gonna be held in. 

        Args:
            name (str): _description_
        """
        
        if name:
            name = self.sanitize_project_name(name)
        
        mesure_dir = self.data.get_data(self.data.Keys.PROJECT_FOLDER_MEASUREMENT, namespace=self.data.Namespaces.PROJECT_MANAGEMENT)
        folder_path = os.path.join(mesure_dir, name)
        
        folder_path = self.get_next_directory_name(folder_path)
        
        # We create the current topmost Measurement Folder here
        self.data.add_data(self.data.Keys.CURRENT_MEASUREMENT_FOLDER, folder_path, namespace=self.data.Namespaces.MEASUREMENT)
        os.makedirs(folder_path)

        # here we create the slots folder structure
        slotnames = self.create_slot_dirs(routinesystem.slots)

        self._create_registry(name)
        
        return slotnames
    
    def create_slot_dirs(self, data: list) -> list:
        """Sets up the slot inside the current Routine Folder.

        Args:
            slot (RoutineData.Slot): The Slot data.
        """
        slotnames = []
        folder_path = self.data.get_data(self.data.Keys.CURRENT_MEASUREMENT_FOLDER, self.data.Namespaces.MEASUREMENT)
        
        if not os.path.exists(folder_path):
            self.logger.error("None existing measurement folder detected.")
            return
        
        for slot in data:
            slotname = slot.name
            if slotname:
                
                slotname = self.sanitize_project_name(slotname)

                slotfolder = os.path.join(folder_path, slotname)
                slotfolder = self.get_next_directory_name(slotfolder)
                
                slotname = os.path.basename(slotfolder)
                slotnames.append(slotname)
                
                os.makedirs(slotfolder)
                
                # Now we register each slot in the resource manager
                self.resman.register_resource(slotname, slotfolder, slotname)
                
                result_folder_path = os.path.join(slotfolder, "Result")
                calibration_folder_path = os.path.join(slotfolder, "Calibration")
                images_folder_path = os.path.join(slotfolder, "Images")
                
                self.resman.register_resource("Result", result_folder_path, slotname)
                self.resman.register_resource("Calibration", calibration_folder_path, slotname)
                self.resman.register_resource("Images", images_folder_path, slotname)
                
                try:
                    os.makedirs(result_folder_path)
                    os.makedirs(calibration_folder_path)
                    os.makedirs(images_folder_path)
                except Exception as e:
                    self.logger.error(f"Could not create all directories in slot {slotname}: {e}")
                    return

                # Sets up the result SQL file
                
                result_db = os.path.join(result_folder_path, "results.db")
                self.resman.register_resource("DB", result_db, slotname)
                self._create_files(slotname, result_db)
         
    def _create_files(self, name: str, filepath: str) -> None:     

        data = {"Name": name, "StartTime": datetime.datetime.now().strftime("%H:%M:%S"), 'Date': datetime.date.today().strftime(r"%d/%m/%Y")}
        table_creation, insert = self.sql.generate_sql_statements("Metadata", data)
        self.sql.read_or_write(filepath, table_creation, "write")
        self.sql.read_or_write(filepath, insert, "write")

    def _create_registry(self, name):
                
        # We check if there is already a measurement register
        sql_path = self.data.get_data(self.data.Keys.MEASUREMENT_REGISTRY_SQL, self.data.Namespaces.PROJECT_MANAGEMENT)
        
        if not os.path.exists(sql_path):
            self.logger.warning("Measurement Registry does not exists.")
            return   
            
        data = {"Name": name, "StartTime": datetime.datetime.now().strftime("%H:%M:%S")}
        table_creation, insert = self.sql.generate_sql_statements("MeasurementRegistry", data)
        self.sql.read_or_write(sql_path, table_creation, "write")
        self.sql.read_or_write(sql_path, insert, "write")
    
    ### Utils
    def get_next_directory_name(self, base_path):
        """
        Finds the next available directory name by checking the existing directories
        and determining the highest numbered suffix.
        """
        dir_name = os.path.basename(base_path)
        parent_dir = os.path.dirname(base_path)

        existing_dirs = [d for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d))]
        pattern = re.compile(rf"^{re.escape(dir_name)}(?: \((\d+)\))?$")

        max_suffix = 0
        for d in existing_dirs:
            match = pattern.match(d)
            if match:
                suffix = match.group(1)
                if suffix:
                    max_suffix = max(max_suffix, int(suffix))
                else:
                    max_suffix = max(max_suffix, 1)

        next_suffix = max_suffix + 1
        if max_suffix == 0:
            return base_path
        else:
            return f"{base_path} ({next_suffix})"
        
    def sanitize_project_name(self, name) -> str:
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