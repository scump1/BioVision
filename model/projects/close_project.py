    
import os

from PySide6.QtWidgets import QMessageBox

from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from operator_mod.logger.global_logger import Logger

from model.utils.resource_manager import ResourceManager

from model.projects.save_project import SaveProject

class CloseProject:

    def __init__(self):

        self.data = InMemoryData()
        self.res_manager = ResourceManager()
        self.logger = Logger("Application").logger

    def close_project(self):

        from view.main.mainframe import MainWindow
        gui_instance = MainWindow.get_instance()

        if self.data.get_data(self.data.Keys.PROJECT_PATH, namespace=self.data.Namespaces.PROJECT_MANAGEMENT):

            # First checking if there are still temp projects in the folder -> Asking to save then
            dirs = os.listdir("model/data/tmp")
            pj_path = self.data.get_data(self.data.Keys.PROJECT_PATH, namespace=self.data.Namespaces.PROJECT_MANAGEMENT)
            pj_name = os.path.basename(pj_path)

            for i in dirs:
                if i == pj_name:

                    dialog = QMessageBox()
                    dialog.setIcon(QMessageBox.Warning)
                    dialog.setWindowTitle("Unsaved Changes")
                    dialog.setText(f"Your project '{pj_name}' has unsaved changes.")
                    dialog.setInformativeText("Would you like to save your changes?")

                    # Add Save and Cancel buttons
                    dialog.setStandardButtons(QMessageBox.Save | QMessageBox.Cancel)
                    dialog.setDefaultButton(QMessageBox.Save)

                    # Show the message box and get the user's response
                    result = dialog.exec()

                    if result == QMessageBox.Save:
                        # Code to save the project
                        saver = SaveProject()
                        saver.save_project()
                    elif result == QMessageBox.Cancel:
                        pass
                    break

            gui_instance.middle_layout.mdi_area.closeAllSubWindows()
            self.data.add_data(self.data.Keys.PROJECT_PATH, None, namespace=self.data.Namespaces.PROJECT_MANAGEMENT)

            # This is just to make sure everything is deleted
            self.data.purge_all_data(namespace=self.data.Namespaces.PROJECT_MANAGEMENT)
            self.res_manager.delete_resource_space("SQLDataBank")
            self.res_manager.delete_resource_space("JSONDataBank")

        else:
            QMessageBox.warning(gui_instance, "No project to close.", "No open project to close.")
