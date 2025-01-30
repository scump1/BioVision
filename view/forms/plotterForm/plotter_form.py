
import os
import datetime

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QListWidget, QListWidgetItem, QSizePolicy, QCheckBox, QPushButton, QToolButton, QMessageBox
from PySide6.QtCore import Qt

from model.utils.SQL.sql_manager import SQLManager
from controller.functions.plotter.plotter import Plotter

from operator_mod.logger.global_logger import Logger
from operator_mod.in_mem_storage.in_memory_data import InMemoryData

class PlotterForm(QWidget):

    def __init__(self) -> None:
        
        super().__init__()

        self.plotter = Plotter()
        self.data = InMemoryData()
        self.sql = SQLManager()

        self.logger = Logger("Application").logger

        self.currplot = None

    def setupForm(self):

        self.layout_wrapper = QHBoxLayout()
        self.layout_wrapper.setContentsMargins(5,5,5,5)

        ### The tabs for the plots
        self.plot_holder_wrapper = QWidget()
        self.plot_holder_wrapper.setMinimumSize(400,300)        
        
        self.plot_holder = QVBoxLayout()
        self.plot_holder_wrapper.setLayout(self.plot_holder)


        ### Rightside interaction layout
        self.rightside_layout_wrapper = QWidget()
        self.rightside_layout_wrapper.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.rightside_layout_wrapper.setMaximumWidth(325)
        self.rightside_layout = QVBoxLayout()
        self.rightside_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.measurement_picker_label = QLabel("Pick a measurement:")

        self.measurement_picker = QComboBox()
        self.measurement_picker.currentTextChanged.connect(lambda: self.parameter_setter(self.measurement_picker.currentText()))

        self.result_picker_label = QLabel("Pick a dataset:")

        self.result_picker = QComboBox()
        self.result_picker.currentTextChanged.connect(lambda: self.result_setter(self.result_picker.currentText()))

        self.rightside_layout.addWidget(self.measurement_picker_label)
        self.rightside_layout.addWidget(self.measurement_picker)
        self.rightside_layout.addWidget(self.result_picker_label)
        self.rightside_layout.addWidget(self.result_picker)

        self.rightside_layout_wrapper.setLayout(self.rightside_layout)

        ### Here we have the picker for x and y

        self.xy_label = QLabel("Choose X and Y Parameter:")

        self.parameter_list = QListWidget()
        self.parameter_list.setMinimumHeight(150)

        self.rightside_layout.addWidget(self.xy_label)
        self.rightside_layout.addWidget(self.parameter_list)

        ### Now we have additional stuff like auto updates and axis titles...

        self.autoupdatecheckbox = QCheckBox("Autoupdates")
        self.rightside_layout.addWidget(self.autoupdatecheckbox)

        ### Now we actually plot
        self.button_layer = QHBoxLayout()

        self.toolbox = QToolButton()
        self.toolbox.setText("...")
        self.plot_button = QPushButton("Plot")
        self.plot_button.clicked.connect(self.plot_button_action)

        self.button_layer.addWidget(self.plot_button)
        self.button_layer.addWidget(self.toolbox)

        self.rightside_layout.addLayout(self.button_layer)

        # Add to the final layout
        self.layout_wrapper.addWidget(self.plot_holder_wrapper)
        self.layout_wrapper.addWidget(self.rightside_layout_wrapper)

        self.setLayout(self.layout_wrapper)

        self.measurement_loader()

    def measurement_loader(self):

        userdata_db_path = os.path.join(self.data.get_data(self.data.Keys.PROJECT_FOLDER_USERDATA, self.data.Namespaces.PROJECT_MANAGEMENT), "userdata.db")

        query = """SELECT Name FROM MeasurementRegistry"""

        result = self.sql.read_or_write(userdata_db_path, query, "read")  # noqa: F841
        
        self.measurement_picker.blockSignals(True)
        for item in result:
            self.measurement_picker.addItem(item[0])
        self.measurement_picker.blockSignals(False)
        
        self.parameter_setter(result[0][0])

    def parameter_setter(self, name):

        ### We would get the measurement table result headers here and classify them as parameters
        # possible_tables = ["environment", "BubbleSizeResults"]

        res_folder = os.path.join(self.data.get_data("ProjectFolderResult"), name)
           
        if os.path.exists(res_folder):

            self.mm_data = os.path.join(res_folder, "data.db")
            query = """SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"""

            result = self.sql.read_or_write(self.mm_data, query, "read")

            # Adding the different results as selection to the picker
            self.result_picker.blockSignals(True)
            self.result_picker.clear()
            for item in result:

                if item[0] == "environment":
                    self.result_picker.addItem("Environment")
                    
                elif item[0] == "BubbleSizeResults":
                    self.result_picker.addItem("Bubble Size Analysis")

            self.result_picker.setCurrentText("Environment")
            self.result_picker.blockSignals(False)

            # Setting the standard
            self.result_setter("Environment")
                    
    def result_setter(self, resultname):

        self.parameter_list.clear()

        if resultname == "Environment":
            self.param_creator(["Time", "Temperature", "Airflow", "Airflow Humidity", "MBR Temperature", "Oxygen", "pH"])

        elif resultname == "Bubble Size Analysis":
            self.param_creator(["CenterX", "CenterY", "MajorAxis", "MinorAxis", "Angle"])

    def param_creator(self, params: list[str]) -> None:

        for param in params:
            param_item = ItemWidget(param)
            listItem = QListWidgetItem(self.parameter_list)
            listItem.setSizeHint(param_item.sizeHint())
            self.parameter_list.addItem(listItem)

            self.parameter_list.setItemWidget(listItem, param_item)

    def plot_button_action(self):

        try:
            x_params = []
            y_params = []

            x_values = []
            y_values = {}

            for i in range(self.parameter_list.count()):
                # Get the widget from the item
                widget = self.parameter_list.itemWidget(self.parameter_list.item(i))
                
                # Check if the xcheck or ycheck checkboxes are checked
                if widget.xcheck.isChecked():
                    x_params.append(widget.label.text())
                if widget.ycheck.isChecked():
                    y_params.append(widget.label.text())

            if len(x_params) > 1:
                from view.main.mainframe import MainWindow

                QMessageBox.warning(MainWindow.get_instance(), "Too many arguments", "Please select only one x-parameter.")
                return
            
            tablename = self.result_picker.currentText()

            for x in x_params:
                if x == "Time":
                    x = "Timestamp"

                    query = f"""SELECT {x} FROM {tablename}"""
                    timestamps = self.sql.read_or_write(self.mm_data, query, "read")

                    # Convert the list of tuples into a list of datetime objects
                    time_objects = [datetime.datetime.strptime(time[0], '%H:%M:%S') for time in timestamps]

                    # Get the first timestamp
                    first_time = time_objects[0]

                    # Calculate the time difference from each timestamp to the first one
                    x_values = [(time - first_time).total_seconds() for time in time_objects]

                else:
                    x = x.replace(" ", "")

                    query = f"""SELECT {x} FROM {tablename}"""
                    result = self.sql.read_or_write(self.mm_data, query, "read")

                    x_values = [value for tup in result for value in tup]

            for i, y in enumerate(y_params):

                if "Time" in y_params:
                    y_params.remove("Time")
                
                y = y.replace(" ", "")

                query = f"""SELECT {y} FROM {tablename}"""
                result = self.sql.read_or_write(self.mm_data, query, "read")

                if result is not None:
                    y_values[y] = [value for tup in result for value in tup]

            if self.currplot is not None:
                self.plot_holder.removeWidget(self.currplot)

            self.currplot = self.plotter.plot(x_values, y_values)
            
            self.plot_holder.addWidget(self.currplot)
        except Exception as e:
            self.logger.error(f"Plotter Form - Error in plotting: {e}")


class ItemWidget(QWidget):

    def __init__(self, text):
        super().__init__()

        layout = QHBoxLayout()

        self.label = QLabel(text)

        self.xcheck = QCheckBox("X")
        self.xcheck.setCheckable(True)
        self.ycheck = QCheckBox("Y")
        self.ycheck.setCheckable(True)

        self.xcheck.setAutoExclusive(True)
        self.ycheck.setAutoExclusive(True)

        layout.addWidget(self.label)
        layout.addWidget(self.xcheck)
        layout.addWidget(self.ycheck)
        self.setLayout(layout)