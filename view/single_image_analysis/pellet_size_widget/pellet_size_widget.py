
import csv
import os
from tkinter import Image
from PySide6.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QTableView, QFileDialog, QMessageBox
from PySide6.QtCore import QThread, Signal, QElapsedTimer
from PySide6.QtGui import QStandardItemModel, QStandardItem

import time
import cv2
import numpy as np

from view.single_image_analysis.graphics_view_widget import ImageDisplaySettings, ImageDisplay

from controller.algorithms.algorithm_manager_class.algorithm_manager import AlgorithmManager
from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from operator_mod.eventbus.event_handler import EventManager
from operator_mod.logger.global_logger import Logger

class ResultWaiter(QThread):
    """Background waiting for finished results and signaling.

    Args:
        QThread (Qt): runs a thread
    """
    progress = Signal(float)
    
    def __init__(self, img_number: int, interval: int) -> None:
        """
        Args: 
            img_number (int): the amount of images that is givem
            interval (int): a msec time interval to wait per image
        """
        super().__init__()
        self.img_num = img_number
        self.interval = interval

    def run(self):
        """Executed on start.
        """
        timer = QElapsedTimer()
        
        timer.start()
        now = 0
        end = self.img_num * self.interval
        while timer.elapsed() < end:
            
            # Every second we emit the signal to increment the progressbar
            r = timer.elapsed()
            if abs(now - r) >= 500:
                self.progress.emit(r/end)
                now = r
                
            time.sleep(0.1)
        
        del timer
            
class PelletSizeWidghet(QTabWidget):

    def __init__(self):
        
        super().__init__()
                
        self.data = InMemoryData()
        self.events = EventManager.get_instance()
        
        self.algman = AlgorithmManager.get_instance()
        
        self.logger = Logger("Application").logger   
        
    def setupForm(self):

        setupWidget = QWidget()
        setuplayout = QVBoxLayout()
        
        ### Image Picker
        # The selector and file path
        selector = QHBoxLayout()
        
        label = QLabel("Choose an image: ")

        calib_dialog_form_button = QPushButton("...")
        calib_dialog_form_button.clicked.connect(self.calib_dialog_button)
        
        selector.addWidget(label)
        selector.addWidget(calib_dialog_form_button)
        
        ### Image Counter
        self.counter = QLabel("Number of selected images: 0")
        
        ### Image Displayer
        imagedisplay_layout = QHBoxLayout()

        imagelayout = QVBoxLayout()
        
        self.imageview = QTabWidget()
        self.imageview.setMinimumSize(400, 600)
        
        delete_image_button = QPushButton("Remove current image from selection")
        delete_image_button.clicked.connect(self._remove_image_button)
        
        imagelayout.addWidget(self.imageview)
        imagelayout.addWidget(delete_image_button)
        
        ### Adding a few custom settings
        
        imagedisplay_layout.addLayout(imagelayout)
        
        # Analyze button and progressbar
        analyze_layout = QVBoxLayout()
        
        startbutton = QPushButton("Analyze")
        startbutton.clicked.connect(self.analyze_button_action)
        
        self.progressbar = QProgressBar()

        analyze_layout.addWidget(startbutton)
        analyze_layout.addWidget(self.progressbar)
        
        ### back to welcome page
        back_to_welcome_page_button = QPushButton("Back")
        back_to_welcome_page_button.clicked.connect(lambda: self.events.trigger_event(self.events.EventKeys.SI_FORM_BACK_BUTTON))
        
        # Stitching together
        setuplayout.addLayout(selector)
        setuplayout.addWidget(self.counter)
        setuplayout.addLayout(imagedisplay_layout)
        setuplayout.addLayout(analyze_layout)
        setuplayout.addWidget(back_to_welcome_page_button)
        
        setupWidget.setLayout(setuplayout)
        
        self.addTab(setupWidget, "Setup")
    
    def analyze_button_action(self) -> None:
        """Action for the analyze button. Checks previous results.
        """
        
        from view.main.mainframe import MainWindow
        instance = MainWindow.get_instance()
        
        # First we check for existing tabs 
        if self.count() > 1:
            result =  QMessageBox.information(instance, "Deleting prior Results", "You have prior results in this form. Do you want to continue?", QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
            
            if not result == QMessageBox.StandardButton.Yes:
                return
            
            while self.count() > 1:
                self.removeTab(self.count() - 1)
        
        filepaths = []
        filesettings = []
        filesizes = []
        for i in range(self.imageview.count()):
            
            widget = self.imageview.widget(i)
            path = widget.path
            
            if os.path.exists(path):
                filepaths.append(path)
                size = os.path.getsize(path)
                filesizes.append(size)
                
                # If there are no settings, its just an empty list
                filesettings.append(widget.settings)
        
        self.data.add_data(self.data.Keys.PELLET_SIZER_IMAGES, filepaths, self.data.Namespaces.DEFAULT)
        self.data.add_data(self.data.Keys.PELLET_SIZER_IMAGE_SETTINGS, filesettings, self.data.Namespaces.DEFAULT)
        self.algman.add_task(self.algman.States.PELLET_SIZER_SINGLE_STATE, 0)
        
        imgnum = self.imageview.count()
        avg_filesize = np.average(filesizes)
        
        waitertime = max(1, min(5, np.sqrt(avg_filesize))) * 1000
        
        self.waiter = ResultWaiter(imgnum, waitertime)
        self.waiter.finished.connect(self.display_results)
        self.waiter.progress.connect(self._progressbar_update)
        self.waiter.start()
    
    ### Result logic
    def display_results(self) -> None:
        """Displays results after analyzing. Called from the WaiterThread by a signal.
        """
        self._progressbar_update(1)
        self._progressbar_update(0)
        
        # Fetching results
        results = self.data.get_data(self.data.Keys.PELLET_SIZER_RESULT, self.data.Namespaces.DEFAULT)
        
        images = []
        data = []
        
        for result in results:
            images.append(result["Image"])
            data.append(result["Data"])
        
        # The images come back in the order of the filepaths given
        filepaths = self.data.get_data(self.data.Keys.PELLET_SIZER_IMAGES, self.data.Namespaces.DEFAULT)
        
        # Creating two widget to fit into QTabWidget
        resultimage_widget = self._result_image_widget(images, filepaths)
        result_table = self._result_table(data, filepaths)
        
        self.addTab(resultimage_widget, "Result Images")
        self.addTab(result_table, "Result Values")
        
        ### Deleting the references to the images of the result to clean up the internal data
        self.data.delete_data(self.data.Keys.PELLET_SIZER_RESULT, self.data.Namespaces.DEFAULT)
        
    def _result_image_widget(self, images: list, filepaths: list) -> QWidget:
        """Prepares a Widget with a TabWidget where the images are shown in ImageDisplays. 

        Args:
            images (list): numpy arrays in a list
            filepaths (list): str paths in a list in the same order as images

        Returns:
            QWidget: return a parent Widget with layout child
        """
        try:
            
            if len(images) != len(filepaths):
                self.logger.critical(f"Result images and given paths do not match.")
                return
            
            widget = QWidget()
            
            layout = QVBoxLayout()
            
            save_button = QPushButton("Save and Export")
            save_button.clicked.connect(lambda: self._result_image_export_button(filepaths))
            
            self.img_stacked_tab = QTabWidget()

            # Adding the images
            for i, image in enumerate(images):
                imgwidget = ImageDisplay(image)
                imgwidget.setupForm()
                
                self.img_stacked_tab.addTab(imgwidget, str(os.path.basename(filepaths[i])))
                
            layout.addWidget(self.img_stacked_tab)
            layout.addWidget(save_button)
            
            widget.setLayout(layout)
            
            return widget  
        
        except Exception as e:
            self.logger.error(f"Error in setting up image displays for results: {e}.") 
    
    def _result_image_export_button(self, filepaths: list) -> None:
        """Exports the resulting images (all/current) as .bmp format.

        Args:
            filepaths (list): str path of images input
        """
        
        from view.main.mainframe import MainWindow
        instance = MainWindow.get_instance()
        
        msg_box = QMessageBox(instance)
        msg_box.setWindowTitle("Export Image(s)")
        msg_box.setText("Do you want to export all images, the current one, or abort?")
        msg_box.setIcon(QMessageBox.Icon.Question)

        # Add buttons
        all_button = msg_box.addButton("All", QMessageBox.ButtonRole.AcceptRole)
        current_button = msg_box.addButton("Current", QMessageBox.ButtonRole.ActionRole)
        abort_button = msg_box.addButton("Abort", QMessageBox.ButtonRole.RejectRole)

        # Execute the dialog
        msg_box.exec()
        
        # Handle the user's choice
        if msg_box.clickedButton() == all_button:
            # Exporting the current image
            dir = QFileDialog.getExistingDirectory(instance, "Choose Directory")

            for i in range(self.img_stacked_tab.count()):
                img_widget = self.img_stacked_tab.widget(i)
                image = img_widget.img

                image_basename = os.path.basename(filepaths[i])
                image_basename = os.path.splitext(image_basename)[0]
                filepath = os.path.join(dir, f"result_image_{image_basename}_{i}.bmp")

                cv2.imwrite(filepath, image)
            
            if os.path.exists(filepath):
                QMessageBox.information(instance, "Success", "Exporting successful.", QMessageBox.StandardButton.Ok)
            else:
                QMessageBox.information(instance, "Error", "Error occured. Please try again.", QMessageBox.StandardButton.Ok)
                
        elif msg_box.clickedButton() == current_button:
            
            # Exporting the current image
            dir = QFileDialog.getExistingDirectory(instance, "Choose Directory")

            idx = self.img_stacked_tab.currentIndex()
            img_widget = self.img_stacked_tab.currentWidget()
            image = img_widget.img
            
            if idx <= len(filepaths):
                image_basename = os.path.basename(filepaths[idx])
                image_basename = os.path.splitext(image_basename)[0]
            else:
                image_basename = "missing_basename"
                
            filepath = os.path.join(dir, f"result_image_{image_basename}.bmp")

            cv2.imwrite(filepath, image)
            
            if os.path.exists(filepath):
                QMessageBox.information(instance, "Success", "Exporting successful.", QMessageBox.StandardButton.Ok)
            else:
                QMessageBox.information(instance, "Error", "Error occured. Please try again.", QMessageBox.StandardButton.Ok)
            
        elif msg_box.clickedButton() == abort_button:
            return        
    
    def _result_table(self, data: list, filepaths: list) -> QWidget:
        """Builds a parent Widget to house the TabResultWidget that contains the TableViews for data on image results.

        Args:
            data (list): data from algorithm PELLETSIZER
            filepaths (list): filepaths for used images

        Returns:
            QWidget: parent widget w/ child TabWidget where results are displayed
        """
        
        try:
            widget = QWidget()
            mainlayout = QVBoxLayout()

            self.stacked_result_tab = QTabWidget()

            # Store references to table models for later access
            self.table_models = []

            for idx, image in enumerate(data):
                table = QTableView()
                model = QStandardItemModel()
                model.setHorizontalHeaderLabels(["Area", "Diameter", "Perimeter"])

                for result in image:
                    row = []
                    for value in result:
                        row.append(QStandardItem(str(value)))

                    model.appendRow(row)

                table.setModel(model)
                self.table_models.append(model)

                self.stacked_result_tab.addTab(table, str(str(os.path.basename(filepaths[idx]))))

            mainlayout.addWidget(self.stacked_result_tab)

            # Add Save Button
            save_button = QPushButton("Save and Export")
            save_button.clicked.connect(lambda: self._save_result_tables(filepaths))  # Connect to the save function
            mainlayout.addWidget(save_button)

            widget.setLayout(mainlayout)

            return widget
        except Exception as e:
            self.logger.error(f"Error setting up result tables: {e}.")
            
    def _save_result_tables(self, filepaths: list) -> None:
        """Exports result tables (all/current) from the TabWidget View on Results.

        Args:
            filepaths (list): str path from the images that have been analyzed
        """
        
        from view.main.mainframe import MainWindow
        instance = MainWindow.get_instance()
        
        msg_box = QMessageBox(instance)
        msg_box.setWindowTitle("Export Table(s)")
        msg_box.setText("Do you want to export all tables, the current one, or abort?")
        msg_box.setIcon(QMessageBox.Icon.Question)

        # Add buttons
        all_button = msg_box.addButton("All", QMessageBox.ButtonRole.AcceptRole)
        current_button = msg_box.addButton("Current", QMessageBox.ButtonRole.ActionRole)
        abort_button = msg_box.addButton("Abort", QMessageBox.ButtonRole.RejectRole)

        # Execute the dialog
        msg_box.exec()
        
        # Handle user's choice
        if msg_box.clickedButton() == all_button:
            # Export all tables
            save_dir = QFileDialog.getExistingDirectory(instance, "Select Directory to Save All Tables")
            if save_dir:
                
                for idx, model in enumerate(self.table_models):
                    image_basename = os.path.basename(filepaths[idx])
                    image_basename = os.path.splitext(image_basename)[0]
                    
                    file_path = os.path.join(save_dir, f"result_table_{image_basename}.csv")
                    self._export_model_to_csv(model, file_path)

                if os.path.exists(file_path):
                    QMessageBox.information(instance, "Success", "Exporting successful.", QMessageBox.StandardButton.Ok)
                else:
                    QMessageBox.information(instance, "Error", "Error occured. Please try again.", QMessageBox.StandardButton.Ok)

        elif msg_box.clickedButton() == current_button:
            
            # Export current table
            current_index = self.stacked_result_tab.currentIndex()
            if current_index >= 0:
                
                image_basename = os.path.basename(filepaths[current_index])
                image_basename = os.path.splitext(image_basename)[0]
                
                file_path, _ = QFileDialog.getSaveFileName(instance, "Save Current Table", f"result_table_{image_basename}.csv", "CSV Files (*.csv)")
                if file_path:
                    self._export_model_to_csv(self.table_models[current_index], file_path)

                if os.path.exists(file_path):
                    QMessageBox.information(instance, "Success", "Exporting successful.", QMessageBox.StandardButton.Ok)
                else:
                    QMessageBox.information(instance, "Error", "Error occured. Please try again.", QMessageBox.StandardButton.Ok)

        elif msg_box.clickedButton() == abort_button:
            # Abort operation
            return        
    
    def _export_model_to_csv(self, model: QStandardItemModel, file_path: str) -> None:
        """Exports a model to a .csv file.

        Args:
            model (QStandardItemModel): Model with data
            file_path (str): str path that is valid
        """
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
                writer = csv.writer(csv_file)

                # Write headers
                headers = [model.horizontalHeaderItem(col).text() for col in range(model.columnCount())]
                writer.writerow(headers)

                # Write data rows
                for row in range(model.rowCount()):
                    row_data = [model.item(row, col).text() for col in range(model.columnCount())]
                    writer.writerow(row_data)

            self.logger.info(f"Exported table to {file_path}.")
        except Exception as e:
            self.logger.error(f"Error exporting table to {file_path}: {e}.")

    def calib_dialog_button(self) -> None:
        """Fetches a list of files that shall be analyzed.
        """
        from view.main.mainframe import MainWindow
        instance = MainWindow.get_instance()
        
        file_paths, _ = QFileDialog.getOpenFileNames(instance, "Open File", "", 
                                             "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff)")
        
        for file_path in file_paths:
            if os.path.exists(file_path):
                
                # the ImageDisplay holds on to the path so we can later just iterate through all widgets and get the paths for the image analysis
                widget = ImageDisplaySettings(file_path)
                widget.setupForm()
                
                self.imageview.addTab(widget, str(os.path.basename(file_path)))
                
                self.imageview.setCurrentIndex(self.imageview.count() - 1)
                self._change_counter(self.imageview.count())
            else:
                self.logger.warning(f"Filepath invalid: {file_path}")
                 
    ### backend logic
    def _progressbar_update(self, value: float):
        """Progresses the progress bar with a given value.

        Args:
            value (float): Value between 0 and 1.
        """
        
        self.progressbar.setValue(int(value * 100))  # Convert to percentage
        self.progressbar.repaint()  # Ensure the UI reflects the change immediately
    
    def _change_counter(self, count: int):
        self.counter.setText(f"Number of selected images: {count}")

    def _remove_image_button(self):
    
        idx = self.imageview.currentIndex()
        
        if idx is not None:
            self.imageview.removeTab(idx)
            self._change_counter(self.imageview.count())