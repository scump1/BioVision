import hashlib
import re
import os
import stat
import uuid
import datetime
import json
import string

from PySide6.QtWidgets import QInputDialog, QMessageBox

from operator_mod.eventbus.event_handler import EventManager
from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from operator_mod.logger.global_logger import Logger

from model.utils.SQL.sql_manager import SQLManager

class NewProject:

    def __init__(self):

        self.data = InMemoryData()
        self.sql_manager = SQLManager()
        self.logger = Logger("Application").logger

        self.event_manager = EventManager.get_instance()

        self.temp_project_path = r"model\data\tmp"
        self.project_path = None

    def new_project(self):

        try:
            # Step 1: Ask for a project name
            self.project_name_getter()

            # Step 2: Create (sub)folders
            self.create_folders(self.project_path)

            # Step 3: Create JSON and config files
            self.create_configs()
            
        except Exception as e:
            self.logger.error(f"ProjectCreation - Error in creating project: {e}")

    def project_name_getter(self):

        from view.main.mainframe import MainWindow

        # A little popup that prompts for a project name
        project_name, ok = QInputDialog.getText(MainWindow.get_instance(), "New Project", "Enter project name:")

        if ok and project_name:
            # Remove invalid characters from project name
            self.project_name = self.sanitize_project_name(project_name)
         
        else:
            # Handle the case where the user cancels or provides no input
            QMessageBox.warning(MainWindow.get_instance(), "Input Error", "Project name cannot be empty or canceled.")
            return
        
        # Now we check if the name is already given and add the affix (x) if true
        self.project_path = self.get_next_directory_name(os.path.join(self.temp_project_path, self.project_name))

        self.data.add_data(self.data.Keys.PROJECT_PATH, self.project_path, namespace=self.data.Namespaces.PROJECT_MANAGEMENT)

    def create_folders(self, path):

        try:
            os.makedirs(path)
            os.chmod(path, stat.S_IWRITE)

            subfolder_link = {
                "Measurement": self.data.Keys.PROJECT_FOLDER_MEASUREMENT,
                "Config": self.data.Keys.PROJECT_FOLDER_CONFIG,
                "UserData": self.data.Keys.PROJECT_FOLDER_USERDATA
            }

            for subfolder in subfolder_link.keys():

                subfolder_path = os.path.join(path, subfolder)
                self.data.add_data(subfolder_link[subfolder], str(subfolder_path), namespace=self.data.Namespaces.PROJECT_MANAGEMENT)
                
                if not os.path.exists(subfolder_path):
                    try:
                        os.makedirs(subfolder_path)     
                    except OSError as e:
                        self.logger.error(f"Error in creating Project: {e}")
                        return None

        except Exception as e:
            self.logger.error(f"Error in creating Project: {e}")
            return None

    def create_configs(self, secretkey="1520387"):

        projectid = str(uuid.uuid4())
        project_hash = hashlib.sha256(str(projectid + secretkey).encode()).hexdigest()

        config_data = {
            "project_id": projectid,
            "project_hash": project_hash,
            "timestamp": datetime.datetime.now().isoformat()
        }

        config_path = self.data.get_data(self.data.Keys.PROJECT_FOLDER_CONFIG, namespace=self.data.Namespaces.PROJECT_MANAGEMENT)
        config_file_path = os.path.join(config_path, "config.json")

        with open(config_file_path, 'w') as config_file:
            json.dump(config_data, config_file, indent=4)

        ### We create the Measurement Register here
        userdata_path = self.data.get_data(self.data.Keys.PROJECT_FOLDER_USERDATA, namespace=self.data.Namespaces.PROJECT_MANAGEMENT)
        sql_file_path = os.path.join(userdata_path, "MeasurementRegister.db")
        
        table, query = self.sql_manager.generate_sql_statements("Metadata", {"Time": datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S")})

        self.sql_manager.read_or_write(sql_file_path, table, "write")
        self.sql_manager.read_or_write(sql_file_path, query, "write")
        
        self.data.add_data(self.data.Keys.MEASUREMENT_REGISTRY_SQL, sql_file_path, self.data.Namespaces.PROJECT_MANAGEMENT)

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
        sanitized_name = ''.join(char if char not in invalid_chars else '' for char in name)
        
        return sanitized_name