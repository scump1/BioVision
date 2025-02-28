
import datetime
import os
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

import time
import cv2

from view.single_image_analysis.graphics_view_widget import ImageDisplay

from controller.algorithms.algorithm_manager_class.algorithm_manager import AlgorithmManager
from model.utils.SQL.sql_manager import SQLManager
from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from operator_mod.eventbus.event_handler import EventManager
from operator_mod.logger.global_logger import Logger

class ResultWaiter(QThread):
    
    progress = Signal(float)
    
    def __init__(self) -> None:
        super().__init__()

    def run(self):
        
        timer = QElapsedTimer()
        
        timer.start()
        now = 0
        while timer.elapsed() < 2000:
            
            # Every second we emit the signal to increment the progressbar
            r = timer.elapsed()
            if abs(now - r) >= 500:
                self.progress.emit(r/500)
                now = r
                
            time.sleep(0.1)
        
        del timer
            
class BubbleSizeWidget(QTabWidget):
    
    def __init__(self):
        
        super().__init__()
        
        self.data = InMemoryData()
        self.events = EventManager.get_instance()
        
        self.algman = AlgorithmManager.get_instance()
        self.sqlmanager = SQLManager()
                
        self.logger = Logger("Application").logger        
        
    def setupForm(self):
        
        setupwidget = QWidget()
        mainlayout = QVBoxLayout()
        
        ### Image Selector Holder
        image_selector_layout = QHBoxLayout()
        
        ### Left Image Selector for Calibration
        calib_layout = QVBoxLayout()
        
        # The selector and file path
        calibselector = QHBoxLayout()
        
        calib_label = QLabel("Calibration Image: ")
        self.calib_line_edit = QLineEdit()
        self.calib_line_edit.setClearButtonEnabled(True)
        
        calib_dialog_form_button = QPushButton("...")
        calib_dialog_form_button.pressed.connect(lambda: self.calib_dialog_button(0))
        
        calibselector.addWidget(calib_label)
        calibselector.addWidget(self.calib_line_edit)
        calibselector.addWidget(calib_dialog_form_button)
        
        # The display unit
        self.calibimg_display = ImageDisplay(None).setupForm()
        self.calibimg_display.setMinimumSize(300, 500)
        
        calib_layout.addLayout(calibselector)
        calib_layout.addWidget(self.calibimg_display)
        
        image_selector_layout.addLayout(calib_layout)
        
        ### Right Image Selector for Target Image
        target_layout = QVBoxLayout()
        
        targetselector = QHBoxLayout()
        
        target_image_label = QLabel("Target Image: ")
        self.target_line_edit = QLineEdit()
        self.target_line_edit.setClearButtonEnabled(True)
        
        target_dialog_form_button = QPushButton("...")
        target_dialog_form_button.pressed.connect(lambda: self.calib_dialog_button(1))
        
        targetselector.addWidget(target_image_label)
        targetselector.addWidget(self.target_line_edit)
        targetselector.addWidget(target_dialog_form_button)
        
        # The display unit
        self.targeting_display = ImageDisplay(None).setupForm()

        target_layout.addLayout(targetselector)
        target_layout.addWidget(self.targeting_display)
        
        image_selector_layout.addLayout(target_layout)
        
        # Start Button
        start_button = QPushButton("Analyze")
        start_button.pressed.connect(self.anaylze_action_button)
        
        self.progressbar = QProgressBar()
        self.progressbar.setRange(0, 100)
               
        mainlayout.addLayout(image_selector_layout)
        mainlayout.addWidget(start_button)
        mainlayout.addWidget(self.progressbar)
        
        # Back Button
        back_to_welcome_page_button = QPushButton("Back")
        back_to_welcome_page_button.pressed.connect(lambda: self.events.trigger_event(self.events.EventKeys.SI_FORM_BACK_BUTTON))
        
        mainlayout.addWidget(back_to_welcome_page_button)
        
        setupwidget.setLayout(mainlayout)
        
        self.addTab(setupwidget, "Setup")
            
    def calib_dialog_button(self, line_edit: int):
        
        from view.main.mainframe import MainWindow
        
        file_path, _ = QFileDialog.getOpenFileName(MainWindow.get_instance(), "Open File", "", "All (*)")
        
        # We sort between calib and target path here using an int
        if file_path and line_edit == 0:
            self.calib_line_edit.setText(file_path)
            self.data.add_data(self.data.Keys.SI_FILEPATH_CALIB, file_path, self.data.Namespaces.DEFAULT)
            
            # Loading the image
            self.calibimg_display.set_image(file_path)
        
        elif file_path and line_edit == 1:
            self.target_line_edit.setText(file_path)
            self.data.add_data(self.data.Keys.SI_FILEPATH_TARGET, file_path, self.data.Namespaces.DEFAULT)
            
            # Loading the image
            self.targeting_display.set_image(file_path)

    def anaylze_action_button(self):
        """Uses the AlgManager to constitute a single image analysis and fetches the results.
        """

        from view.main.mainframe import MainWindow
        
        if len(self.target_line_edit.text()) <= 0:
            QMessageBox.information(MainWindow.get_instance(), "Missing Image", "Please specify a target image.", QMessageBox.StandardButton.Ok)
            return 
        
        # First we check for existing tabs 
        if self.count() > 1:
            result =  QMessageBox.information(MainWindow.get_instance(), "Deleting prior Results", "You have prior results in this form. Do you want to continue?", QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
            
            if not result == QMessageBox.StandardButton.Yes:
                return
            
            while self.count() > 1:
                self.removeTab(self.count() - 1)
                
        # The paths are already in the datastore anyways (see calib dialog button)
        
        self.algman.add_task(self.algman.States.BUBBLE_SIZER_STATE_SINGLE, 0)

        self.worker = ResultWaiter()
        
        self.worker.finished.connect(self._finished_signal_connect)
        self.worker.progress.connect(self._progressbar_update)
        
        self.worker.start()
        # We continue in the function taht is connected to the finished signal below

    def _finished_signal_connect(self):
        
        self.progressbar.reset()
        self.progressbar.setRange(0, 100)
        
        # fetch the results
        results = self.data.get_data(self.data.Keys.SI_RESULT, self.data.Namespaces.DEFAULT)
        data, image = results

        # Now we put the results onto the img and show it
        if data is None or data['Data'] == []:
            
            from view.main.mainframe import MainWindow
            
            QMessageBox.information(MainWindow.get_instance(), "No Result", "The two images do not yield a reasonable result.", QMessageBox.StandardButton.Ok)
            return
        
        imgwidget, tablewidget = self._reconstruct_result_image(data, image)
        
        self.addTab(imgwidget, "Result Image")
        self.addTab(tablewidget, "Result Data")
        
        ### Deleting the result for memeroy management
        self.data.delete_data(self.data.Keys.SI_RESULT, self.data.Namespaces.DEFAULT)
        
    def _progressbar_update(self, value: float):
        """Progresses the progress bar with a given value.

        Args:
            value (float): Value between 0 and 1.
        """
        
        self.progressbar.setValue(int(value * 100))  # Convert to percentage
        self.progressbar.repaint()  # Ensure the UI reflects the change immediately

    def _reconstruct_result_image(self, data, image) -> QWidget:
        """ Loads the target image and reconstructs the ellipse to display in a QGraphicsView.
        
        Args:
            results (MatLike): Result Image
        """
        
        try:
 
            ellipse_list = data["Data"]

            widget = self._setup_visual_result_tab(image)
            tablewidget = self._setup_result_table(ellipse_list)
            
            return widget, tablewidget

        except Exception as e:
            
            self.logger.warning(f"Error in displaying results: {e}.")
            
    def _setup_visual_result_tab(self, image: str | list) -> QWidget:
        """Sets up the visual result in a QGraphicsForm and paints ellipses above it using cv2.
        
        Args:
            image (str | MatLike): The resulting image of an analysis either as path or MatLike
            
        Return:
            widget (QWidget): A wrapper widget that returns a image holder and a save functionality
        """
        try:
            mainwidget = QWidget()
            mainlayout = QVBoxLayout()
            
            # The display unit
            widget = ImageDisplay(image)
            widget.setupForm()
            
            # The save button
            savebutton = QPushButton("Save Image")
            savebutton.pressed.connect(lambda: self._save_result_img_button_action(image))
                    
            mainlayout.addWidget(widget)
            mainlayout.addWidget(savebutton)
            
            mainwidget.setLayout(mainlayout)
            
            return mainwidget
        
        except Exception as e:
            self.logger.warning(f"Could not create result image tab: {e}.")
    
    def _save_result_img_button_action(self, img):
        
        from view.main.mainframe import MainWindow
        
        directorypath = QFileDialog.getExistingDirectory(MainWindow.get_instance(), "Target Directory", "")
        
        if os.path.exists(directorypath):
            
            try:
                today = datetime.datetime.today().strftime("%d_%m_%Y_%H_%M_%S")
                resultname = f"Image_Result_{today}.bmp"
                targetpath = os.path.join(directorypath, resultname)
                cv2.imwrite(targetpath, img)
                
            except Exception as e:
                self.logger.error(f"Could not write image to path: {targetpath} with error: {e}.")
                QMessageBox.warning(MainWindow.get_instance(), "Error occured", "Could not write the image to target directory.", QMessageBox.StandardButton.Ok)  
    
    def _setup_result_table(self, results) -> QWidget:
        """Takes the results and displays them in a table view.
        """
        try:
            widget = QWidget()
            mainlayout = QVBoxLayout()
            
            table = QTableView()
            
            save_button = QPushButton("Save Results")
            save_button.pressed.connect(lambda: self._save_result_table_button_action(results))
            
            model = QStandardItemModel()
            model.setHorizontalHeaderLabels(["CenterX", "CenterY", "EquivalentDiameter", "Area", "SurfaceArea", "Volume", "SpecificSurfaceVolume", "SauterDiameter", "Circularity"])

            for item in results:
                row = []
                for value in item:
                    row.append(QStandardItem(str(value)))
                    
                model.appendRow(row)
                
            table.setModel(model)
            
            mainlayout.addWidget(table)
            mainlayout.addWidget(save_button)
            
            widget.setLayout(mainlayout)
            
            return widget
        except Exception as e:
            self.logger.warning(f"Creating result tab failed: {e}.")
    
    def _save_result_table_button_action(self, results) -> None:
        
        from view.main.mainframe import MainWindow
        
        directorypath = QFileDialog.getExistingDirectory(MainWindow.get_instance(), "Target Directory", "")

        if os.path.exists(directorypath):
            
            try:
                today = datetime.datetime.today().strftime("%d_%m_%Y_%H_%M_%S")
                
                resultname = f"result_data_{today}.db"
                filepath = os.path.join(directorypath, resultname)
                
                keys = ["CenterX", "CenterY", "EquivalentDiameter", "Area", "SurfaceArea", "Volume", "SpecificSurfaceVolume", "SauterDiameter", "Circularity"]
                data_dict = {}
                
                for ellipse in results:
                    
                    if not ellipse:
                        for i, key in enumerate(keys):
                            data_dict[key] = "Faulty Data"
                    else:
                        for i, key in enumerate(keys):
                            data_dict[key] = ellipse[i]
                
                    table, insert = self.sqlmanager.generate_sql_statements("Results", data_dict)
                    
                    self.sqlmanager.read_or_write(filepath, table, "write")
                    self.sqlmanager.read_or_write(filepath, insert, "write")                                
                
            except Exception as e:
                self.logger.warning(f"Could not save results: {e}.")