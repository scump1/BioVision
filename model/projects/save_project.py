
import os
import shutil

from PySide6.QtWidgets import QFileDialog, QMessageBox

from operator_mod.logger.global_logger import Logger
from operator_mod.in_mem_storage.in_memory_data import InMemoryData

from model.utils.resource_manager import ResourceManager

class SaveProject:

    def __init__(self):

        self.data = InMemoryData()
        self.logger = Logger("Application").logger

        self.res_man = ResourceManager()

    def save_pretend(self):

        from view.main.mainframe import MainWindow

        pj_path = self.data.get_data(self.data.Keys.PROJECT_PATH, namespace=self.data.Namespaces.PROJECT_MANAGEMENT)
        if pj_path is None:
            QMessageBox.warning(MainWindow.get_instance(), "No open project.", "Please open a project to save it.")
            return None

        try:
            QMessageBox.information(MainWindow.get_instance(), "Saved successfully.", "Project saved successfully.")
        except Exception as e:
            QMessageBox.critical(MainWindow.get_instance(), "Unknown error.", f"Unknown error occured: {e}.")

    def save_project(self):
       
        from view.main.mainframe import MainWindow

        pj_path = self.data.get_data(self.data.Keys.PROJECT_PATH, namespace=self.data.Namespaces.PROJECT_MANAGEMENT)
        if pj_path is None:
            QMessageBox.warning(MainWindow.get_instance(), "No open project.", "Please open a project to save it.")
            return None

        try:
            # Get directory path using QFileDialog
            dir_path = QFileDialog.getExistingDirectory(MainWindow.get_instance(), "Select Project Directory to Save")
            
            if not dir_path:
                return

            pj_path = self.data.get_data(self.data.Keys.PROJECT_PATH, namespace=self.data.Namespaces.PROJECT_MANAGEMENT)
            pj_name = os.path.basename(pj_path)

            # Rewriting the project paths
            new_path = os.path.join(dir_path, pj_name)
            self.data.add_data(self.data.Keys.PROJECT_PATH, new_path, namespace=self.data.Namespaces.PROJECT_MANAGEMENT)

            # Why not a dict here?
            subfolders = ["Measurement", "Config", "UserData"]
            intern_subfolder = [self.data.Keys.PROJECT_FOLDER_MEASUREMENT, self.data.Keys.PROJECT_FOLDER_CONFIG, self.data.Keys.PROJECT_FOLDER_USERDATA]

            for i, subfolder in enumerate(subfolders):

                subfolder_path = os.path.join(new_path, subfolder)
                self.data.add_data(intern_subfolder[i], str(subfolder_path), namespace=self.data.Namespaces.PROJECT_MANAGEMENT)

            # Here we should move the MeasurementRegistry Later
            old_registry_path = self.data.get_data(self.data.Keys.MEASUREMENT_REGISTRY_SQL, self.data.Namespaces.PROJECT_MANAGEMENT)
            registry_basename = os.path.basename(old_registry_path)
            
            userdata = self.data.get_data(self.data.Keys.PROJECT_FOLDER_USERDATA, self.data.Namespaces.PROJECT_MANAGEMENT)
            
            new_registry_path = os.path.join(userdata, registry_basename)
            self.data.add_data(self.data.Keys.MEASUREMENT_REGISTRY_SQL, new_registry_path, self.data.Namespaces.PROJECT_MANAGEMENT)

            # Move the project directory
            shutil.move(pj_path, dir_path)
            self.res_man.register_resource(os.path.basename(dir_path), dir_path, "SaveLocations")

        except Exception as e:
            QMessageBox.critical(MainWindow.get_instance(), "Error while saving.", f"Error occured: {e}.")