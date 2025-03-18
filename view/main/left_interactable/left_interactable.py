import os
import stat
from pathlib import Path
import subprocess
import re
import uuid

from PySide6.QtWidgets import QSplitter, QInputDialog, QFileSystemModel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QTabWidget, QListView, QGridLayout, QLabel, QMdiSubWindow
from PySide6.QtGui import QIcon, QCloseEvent
from PySide6.QtCore import Qt, QTimer, QFileInfo, QSize, QSortFilterProxyModel

from view.databasefileForm.database_form import DataBaseForm
from view.imageviewForm.imageview_form import ImageViewer

from model.utils.SQL.sql_manager import SQLManager

from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from operator_mod.eventbus.event_handler import EventManager
from operator_mod.logger.global_logger import Logger

class LeftInteractable(QVBoxLayout):

    def __init__(self):

        super().__init__()

        self.data = InMemoryData()
        self.events = EventManager()
        self.sql = SQLManager()
        self.logger = Logger("Application").logger

        self.excluded_folders = ["Config", "UserData"]

        self.old_pjpath = None

        # The static list of devices that we use
        self.devices = ["Arduino", "Camera", "MFC", "Pump"]
        self.old_connected_devices = None

        # This timer controls both the device manager and the project explorer
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.model_updater)
        self.timer.timeout.connect(self.device_manager_updater)
        self.timer.start()

    def interactable(self):

        self.left_splitter = QSplitter(Qt.Vertical)
        self.left_splitter.setMinimumWidth(250)
        
        # Setup off the Project Explorer and its logic
        self.setup_project_explorer()
        
        # Setup the Device Manager
        self.setup_device_manager()

        self.left_splitter.addWidget(self.project_explorer_wrapper)
        self.left_splitter.addWidget(self.device_manager_wrapper)

        self.addWidget(self.left_splitter)

        return self
    
    def setup_device_manager(self):
        # This displays all connected devices and their information
        self.device_manager_wrapper = QTabWidget()
        self.device_manager_wrapper.setMinimumHeight(250)

        self.grid_widget = QWidget()
        
        self.device_manager = QGridLayout()

        # Set column stretch factors
        self.device_manager.setColumnStretch(0, 2)  # Device name column
        self.device_manager.setColumnStretch(1, 1)  # Status label column

        # Setup of the grid layout
        for i, device in enumerate(self.devices):
            name_label = QLabel(device)  # Device name label
            self.device_manager.addWidget(name_label, i, 0)  # Column 0 for name
            
            status_label = QLabel()  # Status label
            self.device_manager.addWidget(status_label, i, 1)  # Column 1 for status
        
        self.status_labels = [self.device_manager.itemAtPosition(i, 1).widget() for i in range(len(self.devices))]

        self.grid_widget.setLayout(self.device_manager)
        self.device_manager_wrapper.addTab(self.grid_widget, "Device Manager")

    def setup_project_explorer(self):

         # This widget display all measurments and results from a project
        self.project_explorer_wrapper = QTabWidget()
        self.project_explorer_wrapper.setAcceptDrops(True)

        ## This holds all the widgets and layouts
        self.wrapper_widget = QWidget()
        self.wrapper_widget.setAcceptDrops(True)

        self.general_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()
        self.button_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.file_model = CustomFileSystemModel(self.excluded_folders)

        self.proxy_model = FolderFilterProxyModel(self.excluded_folders)
        self.proxy_model.setSourceModel(self.file_model)

        self.project_explorer = QListView()
        self.project_explorer.setAcceptDrops(True)
        self.project_explorer.doubleClicked.connect(lambda index: self.on_double_click(index))

        # All the buttons that we need for the interactions
        self.back_button = QPushButton()
        self.back_button.setFixedSize(QSize(25, 25))
        self.back_button.setIcon(QIcon(r"view\main\left_interactable\resources\back-button.png"))
        self.back_button.clicked.connect(self.back_button_action)

        self.forward_button = QPushButton()
        self.forward_button.setFixedSize(QSize(25, 25))
        self.forward_button.setIcon(QIcon(r"view\main\left_interactable\resources\forward_button.png"))
        self.forward_button.clicked.connect(self.forward_button_action)

        self.newfolder_button = QPushButton()
        self.newfolder_button.setFixedSize(QSize(25, 25))
        self.newfolder_button.setIcon(QIcon(r"view\main\left_interactable\resources\new-tab.png"))
        self.newfolder_button.clicked.connect(self.newfolder_button_action)

        ### Adding a delete folder functionality here
        self.delete_folder_button = QPushButton()
        self.delete_folder_button.setFixedSize(QSize(25, 25))
        self.delete_folder_button.setIcon(QIcon(r"view\main\left_interactable\resources\trash-can.png"))
        self.delete_folder_button.clicked.connect(self.delete_folder_button_action)

        self.explorer_button = QPushButton()
        self.explorer_button.setFixedSize(QSize(25, 25))
        self.explorer_button.setIcon(QIcon(r"view\main\left_interactable\resources\arrow-up-right-from-square.png"))
        self.explorer_button.clicked.connect(self.explorer_open_action)

        self.button_layout.addWidget(self.back_button)
        self.button_layout.addWidget(self.forward_button)
        self.button_layout.addWidget(self.newfolder_button)
        self.button_layout.addWidget(self.delete_folder_button)
        self.button_layout.addWidget(self.explorer_button)

        self.general_layout.addLayout(self.button_layout)
        self.general_layout.addWidget(self.project_explorer)

        self.wrapper_widget.setLayout(self.general_layout)

        self.project_explorer_wrapper.addTab(self.wrapper_widget, "Project Explorer")

    def back_button_action(self):

        curridx = self.project_explorer.currentIndex()
        currpath = self.file_model.filePath(self.proxy_model.mapToSource(curridx))
        parentidx = self.proxy_model.parent(curridx)
        
        if parentidx.isValid() and (currpath != self.data.get_data(self.data.Keys.PROJECT_PATH, namespace=self.data.Namespaces.PROJECT_MANAGEMENT)):
            self.project_explorer.setRootIndex(parentidx)
            self.project_explorer.setCurrentIndex(parentidx)

    def forward_button_action(self):

        # Get the list of selected indexes
        selected_indexes = self.project_explorer.selectedIndexes()
        
        if selected_indexes:
            # Assume single selection mode, so get the first selected index
            selected_index = selected_indexes[0]
            
            # Check if the selected index is a directory
            if self.file_model.isDir(self.proxy_model.mapToSource(selected_index)):
                # Set the QListView's root index to the selected directory
                self.project_explorer.setRootIndex(selected_index)
                self.project_explorer.setCurrentIndex(selected_index)

    def newfolder_button_action(self):

        from view.main.mainframe import MainWindow

        # Get the current index and path
        curridx = self.project_explorer.currentIndex()
        currpath = self.file_model.filePath(self.proxy_model.mapToSource(curridx))

        # Create the new folder
        folder_name, ok = QInputDialog.getText(MainWindow.get_instance(), "New Folder", "Enter a folder name:")

        if ok and folder_name:
            pjpath = self.data.get_data(self.data.Keys.PROJECT_PATH, namespace=self.data.Namespaces.PROJECT_MANAGEMENT)
            if currpath:
                self.folder_name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', folder_name)
                path = os.path.join(currpath, folder_name)
            else:
                self.folder_name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', folder_name)
                path = os.path.join(pjpath, folder_name)
            os.makedirs(path)
            os.chmod(path, stat.S_IWRITE) 

    def delete_folder_button_action(self):
        
        curridx = self.project_explorer.currentIndex()
        currpath = self.file_model.filePath(self.proxy_model.mapToSource(curridx))
        
        print(currpath)

    def explorer_open_action(self):

        curridx = self.project_explorer.currentIndex()
        currpath = self.file_model.filePath(self.proxy_model.mapToSource(curridx))

        try:
            if currpath:
                if not os.path.exists(currpath):
                    self.logger.critical("Project Explorer - If this happens were fucked.")
                else:
                    # Open File Explorer
                    subprocess.run(['explorer', str(Path(currpath))], check=True)
        except Exception as e:
            self.logger.warning(f"Project Explorer - Error in opening the File Explorer: {e}")

    def on_double_click(self, index):

        from view.main.mainframe import MainWindow

        path = self.file_model.filePath(self.proxy_model.mapToSource(index))
        name = os.path.basename(path)
        fileinfo = QFileInfo(path)
        
        if fileinfo.isDir():
            self.project_explorer.setRootIndex(index)

        elif fileinfo.suffix() == "db":

            self.main = MainWindow.get_instance()

            self.databaseform = DataBaseForm(path, uuid.uuid4())
            self.databaseform.setupForm()
            self.databaseform.load_data()

            subWindow = QMdiSubWindow()
            subWindow.setWidget(self.databaseform)
            subWindow.setWindowTitle(f"Viewing database: {name}")
            subWindow.setMinimumSize(400, 400)

            self.main.middle_layout.mdi_area.addSubWindow(subWindow)
            subWindow.show()

        elif fileinfo.suffix() == "bmp" or "png" or "jpg" or "jpeg":

            self.main = MainWindow.get_instance()

            self.img_form = ImageViewer(path)
            self.img_form.setupForm()
            
            subWindow = QMdiSubWindow()
            subWindow.setWidget(self.img_form)
            subWindow.setWindowTitle(f"Image: {name}")

            self.main.middle_layout.mdi_area.addSubWindow(subWindow)
            subWindow.show()

        else:
            pass
            
    def model_updater(self, path=None):

        if path is None:

            pjpath = self.data.get_data(self.data.Keys.PROJECT_PATH, namespace=self.data.Namespaces.PROJECT_MANAGEMENT)

            if pjpath is None:
                self.project_explorer.setModel(None)
                return
            # First we check if we have a new project opened
            if pjpath != self.old_pjpath:
                self.file_model.setRootPath(pjpath)
                self.project_explorer.setModel(self.proxy_model)
                self.project_explorer.setRootIndex(self.proxy_model.mapFromSource(self.file_model.index(pjpath)))

                self.old_pjpath = pjpath

    def device_manager_updater(self):
        connected_devices = self.data.get_data(self.data.Keys.CONNECTED_DEVICES, namespace=self.data.Namespaces.CONTROLLER)
        
        if connected_devices != self.old_connected_devices:
            
            if connected_devices is None:
                connected_devices = []

            for i, device in enumerate(self.devices):
                status = device in connected_devices if connected_devices else False
                if status:
                    self.status_labels[i].setText("Connected")
                    self.status_labels[i].setStyleSheet("color: green;")
                else:
                    self.status_labels[i].setText("Disconnected")
                    self.status_labels[i].setStyleSheet("color: red;")

            self.old_connected_devices = connected_devices

    def closeEvent(self, event: QCloseEvent):

        try:
            if self.timer.isActive():
                self.timer.stop()
        finally:
            event.accept()

class CustomFileSystemModel(QFileSystemModel):
    def __init__(self, excluded_folders=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.excluded_folders = excluded_folders if excluded_folders is not None else []

    def filterAcceptsRow(self, sourceRow, sourceParent):
        index = self.index(sourceRow, 0, sourceParent)
        if not index.isValid():
            return False
        
        file_path = self.filePath(index)
        for folder in self.excluded_folders:
            if folder in file_path:
                return False
        return True

class FolderFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, excluded_folders=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.excluded_folders = excluded_folders if excluded_folders is not None else []

    def filterAcceptsRow(self, sourceRow, sourceParent):
        model = self.sourceModel()
        index = model.index(sourceRow, 0, sourceParent)
        if not index.isValid():
            return False
        
        file_path = model.filePath(index)
        for folder in self.excluded_folders:
            if folder in file_path:
                return False
        return True