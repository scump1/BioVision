import os
import json
import hashlib

from PySide6.QtWidgets import QFileDialog, QMessageBox

from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from operator_mod.logger.global_logger import Logger

from model.data.configuration_manager import ConfigurationManager
from model.utils.resource_manager import ResourceManager

class OpenProject:

    def __init__(self):

        self.data = InMemoryData()
        self.logger = Logger("Application").logger

        self.configuration = ConfigurationManager()
        self.res_manager = ResourceManager()

    def open_project(self, secretkey="1520387"):

        from view.main.mainframe import MainWindow

        dir_path = QFileDialog.getExistingDirectory(MainWindow.get_instance(), "Select Project Directory")

        config_file_path = os.path.join(dir_path, "Config", "config.json")
        if not os.path.exists(config_file_path):
            QMessageBox.critical(MainWindow.get_instance(), "Invalid folder.", "Please select a valid folder.")
            return None

        with open(config_file_path, 'r') as config_file:
            config_data = json.load(config_file)

        project_id = str(config_data["project_id"])
        stored_hash = config_data["project_hash"]
        computed_hash = hashlib.sha256(str(project_id + secretkey).encode()).hexdigest()
        
        if computed_hash != stored_hash:

            QMessageBox.critical(MainWindow.get_instance(), "Invalid folder.", "Please select a valid folder.")
            return None

        else:

            ### recreating all the paths
            self.data.add_data(self.data.Keys.PROJECT_PATH, dir_path, namespace=self.data.Namespaces.PROJECT_MANAGEMENT)

            subfolder_link = {
                "Measurement": self.data.Keys.PROJECT_FOLDER_MEASUREMENT,
                "Config": self.data.Keys.PROJECT_FOLDER_CONFIG,
                "UserData": self.data.Keys.PROJECT_FOLDER_USERDATA
            }
            
            for subfolder in subfolder_link.keys():

                subfolder_path = os.path.join(dir_path, subfolder)
                self.data.add_data(subfolder_link[subfolder], str(subfolder_path), namespace=self.data.Namespaces.PROJECT_MANAGEMENT)

        # We check for existing resources
        path = self.data.get_data(self.data.Keys.PROJECT_FOLDER_USERDATA, namespace=self.data.Namespaces.PROJECT_MANAGEMENT)
        self.check_resources(path)

    def check_resources(self, path):

        if os.path.exists(path) and os.path.isdir(path):
        
            # List all files in the directory (no recursion)
            for file in os.listdir(path):
                filepath = os.path.join(path, file)
                
                if file.endswith(".db"):
                    self.data.add_data(self.data.Keys.MEASUREMENT_REGISTRY_SQL, filepath, self.data.Namespaces.PROJECT_MANAGEMENT)
                    
                elif file.endswith(".json"):

                    # If the necessarz file exists we can just load it directlz from the configuration manager
                    if file == 'device_configuration.json':
                        self.configuration.load_configuration()

                    self.res_manager.register_resource(file, filepath, "JSONDataBank")