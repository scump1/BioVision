import tempfile
import os
import shutil

from PySide6.QtWidgets import QWidget, QTableView, QVBoxLayout, QPushButton, QComboBox
from PySide6.QtSql import QSqlDatabase, QSqlTableModel

from model.utils.SQL.sql_manager import SQLManager
from model.utils.file_access.file_access_manager import FileAccessManager

from operator_mod.logger.global_logger import Logger
from operator_mod.in_mem_storage.in_memory_data import InMemoryData


class DataBaseForm(QWidget):

    def __init__(self, path, uid) -> None:
        super().__init__()

        self.sql = SQLManager()
        self.file_access = FileAccessManager()
        self.data = InMemoryData()
        self.logger = Logger("Application").logger

        self.uid = uid
        self.path = path
        if not os.path.exists(self.path):
            self.logger.error(f"Application - DatabaseForm - The database path {self.path} does not exist.")
            return

        self.temp_path = None  # Start without a path to temporary copy
        self.new_temp_path = None
        self.db = None

        self.current_index = 0

        self.tables = set()

    def setupForm(self):
        self.mainlayout = QVBoxLayout()

        self.refresh_button = QPushButton('Refresh')
        self.refresh_button.clicked.connect(self.load_data)
        self.mainlayout.addWidget(self.refresh_button)

        self.comboBox = QComboBox()
        self.comboBox.currentIndexChanged.connect(self.on_combobox_index_changed)
        self.mainlayout.addWidget(self.comboBox)

        self.table_view = QTableView()
        self.table_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.mainlayout.addWidget(self.table_view)

        self.setLayout(self.mainlayout)

    def create_temp_copy(self):
        
        try:            
            
            # Create a new temp file path and copy database
            fd, self.new_temp_path = tempfile.mkstemp(suffix=".sqlite")
            os.close(fd)  # Close the file descriptor since we only need the path
            self.file_access.get_access(self.path)
            shutil.copyfile(self.path, self.new_temp_path)
            
            if self.db is None:
                conn_name = f'unique_connection_{self.uid}'
                self.db = QSqlDatabase.addDatabase('QSQLITE', conn_name)
        
            self.db.setDatabaseName(self.new_temp_path)
            
            if not self.db.open():
                self.logger.error(f'Error in DataForm loadTable: Unable to open {self.temp_path}')
                return

            if self.temp_path:
                os.remove(self.temp_path)  # Clean up any previous copy
                
            self.temp_path = self.new_temp_path    

            self.logger.info(f"Copied database to {self.temp_path}")
            
        except Exception as e:
            self.logger.error(f"Error copying database: {e}")
        finally:
            self.file_access.release_access(self.path)

    def load_data(self):

        if not os.path.exists(self.path):
            self.logger.error(f'Error in DataForm loadTable: {self.path} does not exist')
            return
        
        self.create_temp_copy()

        self.refresh_button.blockSignals(True)
        self.comboBox.blockSignals(True)

        self.tables = set(self.db.tables())

        # Refresh ComboBox with the available tables
        self.comboBox.clear()
        self.comboBox.addItems(self.tables)

        # Restore the previously selected table if it still exists
        if self.current_index < len(self.tables):
            self.comboBox.setCurrentIndex(self.current_index)
        else:
            self.comboBox.setCurrentIndex(0)

        self.refresh_button.blockSignals(False)
        self.comboBox.blockSignals(False)

        # Update the table view
        self.update_table_view()

    def on_combobox_index_changed(self, index):
        
        if index == self.current_index:
            return  # Avoid redundant updates if the index hasn't changed
        self.current_index = index
        self.update_table_view()

    def update_table_view(self):
        
        if self.db and self.db.isOpen():
            model = QSqlTableModel(self, self.db)
            model.setTable(self.comboBox.currentText())
            model.select()
            self.table_view.setModel(model)

    def closeEvent(self, event):
        try:

            # Ensure the model is detached from the view to prevent database locking
            self.table_view.setModel(None)  # Clear model from the table view
            self.tables.clear()
          
            # Close Database Connection if open
            if self.db and self.db.isOpen():
                self.db.close()           
                
            # Close temp file and remove it if it exists
            if self.temp_path and os.path.exists(self.temp_path):
                os.remove(self.temp_path)
            
            # We gracefully remove the subwindow when its closed here
            from view.main.mainframe import MainWindow

            inst = MainWindow.get_instance()
            subwindows = inst.middle_layout.mdi_area.subWindowList()

            for subwindow in subwindows:
                if isinstance(subwindow.widget(), DataBaseForm):
                    widget = subwindow.widget()
                    if widget.uid == self.uid:
                        inst.middle_layout.mdi_area.removeSubWindow(subwindow)
            
            # Clean up data in memory
            self.logger.info("DatabaseForm closed and cleaned up successfully.")

        except Exception as e:
            self.logger.warning(f"Error in DataForm Cleanup: {e}")
        
        finally:
            event.accept()
