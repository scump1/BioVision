
import os
import re
import string

from operator_mod.logger.global_logger import Logger
from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from model.utils.SQL.sql_manager import SQLManager
from model.utils.resource_manager import ResourceManager

class MixingTimeCreator:
    
    def __init__(self):
        
        self.logger = Logger("Application").logger
        self.data = InMemoryData()
        self.sql = SQLManager()
        self.resman = ResourceManager()
    
    def create_file_structures(self, name: str):
        """Creates appropiate file structures for the mixing time measurement.

        Args:
            name (str): the measurement name
        """
        
        if name:
            name = f'MT_{self.sanitize_project_name(name)}'
        
        mesure_dir = self.data.get_data(self.data.Keys.PROJECT_FOLDER_MEASUREMENT, namespace=self.data.Namespaces.PROJECT_MANAGEMENT)
        folder_path = os.path.join(mesure_dir, name)
        
        folder_path = self.get_next_directory_name(folder_path)
        
        # We create the current topmost Measurement Folder here
        self.data.add_data(self.data.Keys.CURRENT_MIXINGTIME_FOLDER, folder_path, namespace=self.data.Namespaces.MIXING_TIME)
        os.makedirs(folder_path)
        
        self.create_subfolders(folder_path)
    
    def create_subfolders(self, folder: str):
        """Creates the appropiate subfolders for data storage.

        Args:
            folder (str): the created folder path
        """
        
        subfolder = {
            'Calibration': self.data.Keys.CURRENT_MIXINGTIME_FOLDER_CALIBRATION,
            'Images': self.data.Keys.CURRENT_MIXINGTIME_FOLDER_IMAGES,
            'Data': self.data.Keys.CURRENT_MIXINGTIME_FOLDER_DATA
        }
        
        # Create the subfolders
        for subfolder, key in subfolder.items():
            subfolder_path = os.path.join(folder, subfolder)
            self.data.add_data(key, subfolder_path, namespace=self.data.Namespaces.MIXING_TIME)
            os.makedirs(subfolder_path)
    
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