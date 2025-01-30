
import csv
import os

from PySide6.QtWidgets import QMessageBox

from view.main.mainframe import MainWindow
from view.databasefileForm.database_form import DataBaseForm

from operator_mod.eventbus.event_handler import EventManager
from operator_mod.logger.global_logger import Logger
from model.utils.SQL.sql_manager import SQLManager

class FileExporter:
    
    def __init__(self) -> None:
        self.events = EventManager()
        self.sql = SQLManager()

        self.logger = Logger("Application").logger
    
    def export_as_csv(self):

        try:

            instance = MainWindow.get_instance()
            subwindow = instance.middle_layout.mdi_area.currentSubWindow()

            widget = subwindow.widget()

            if isinstance(widget, DataBaseForm):
                
                dbpath = widget.path
                tablename = widget.comboBox.currentText()

                query = f"""PRAGMA table_info({tablename})"""

                result = self.sql.read_or_write(dbpath, query, "read")
                
                if result:

                    head, _ = os.path.split(dbpath)
                    csvpath = os.path.join(head, "csv_export.csv")

                    with open(csvpath, "w", newline='') as csvfile:

                        columns = [info[1] for info in result]

                        writer = csv.writer(csvfile)
                        writer.writerow(columns)

                        # Fetch and write the entire table data
                        query = f"SELECT * FROM {tablename}"
                        data = self.sql.read_or_write(dbpath, query, "read")
                        if data:
                            writer.writerows(data)

            else:
                QMessageBox.information(instance, "Wrong subwindow", "Please select a Database View as active window.")

        except Exception as e:
            self.logger.warning(f"TB - Error in exporting as csv: {e}.")