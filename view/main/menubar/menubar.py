from ast import Set
import os

from PySide6.QtWidgets import QMenu, QMenuBar, QMdiSubWindow, QMessageBox
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtCore import QTimer

from model.utils.SQL.sql_manager import SQLManager

from operator_mod.eventbus.event_handler import EventManager
from operator_mod.in_mem_storage.in_memory_data import InMemoryData

class MenuBar(QMenuBar):

    def __init__(self):

        super().__init__()

        self.events = EventManager()
        self.data = InMemoryData()
        self.sql = SQLManager()
        
        self.project_open = None
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.options_updater)
        self.timer.start(250)

    def menuBar(self):

        # Adding all the action(s)
        
        # First the "File" menu for new projects, measurements and more
        self.menuProject = QMenu("Project", self)
        ## The "New" selector for: Project, Measurement with subcategories "Technical" and "Cultivation"
        self.menuNew = QMenu("New", self)
        
        self.actionProject = QAction("Project", self)
        self.actionProject.triggered.connect(lambda : self.events.trigger_event(self.events.EventKeys.GUI_NEW_PROJECT)) 

        # Measurements related stuff
        self.menuMeasurement = QAction("Measurement", self)
        self.menuMeasurement.triggered.connect(self.measurement_action)

        self.menuMixingTime = QAction("Mixing Time", self)
        self.menuMixingTime.triggered.connect(self.mixing_time_action)

        # Live View
        self.live_view = QAction("Live View", self)
        self.live_view.triggered.connect(self.live_view_action)
        
        # The single image analysis tool
        self.single_image_analysis = QAction("Image Analysis", self)
        self.single_image_analysis.triggered.connect(self.single_image_analysis_action)

        self.menuNew.addAction(self.actionProject)
        self.menuProject.addAction(self.menuNew.menuAction())
        self.menuNew.addAction(self.menuMeasurement)
        self.menuNew.addAction(self.menuMixingTime)
        self.menuNew.addAction(self.live_view)
        self.menuNew.addAction(self.single_image_analysis)

        self.actionSettings = QAction("Settings", self)
        self.actionSettings.triggered.connect(self.project_setting)
        self.menuProject.addAction(self.actionSettings)

        ## Seperator
        self.menuProject.addSeparator()

        ## Open / Close Projects
        self.actionOpen = QAction("Open Project", self)
        self.actionOpen.triggered.connect(lambda: self.events.trigger_event(self.events.EventKeys.GUI_OPEN_PROJECT))

        self.actionClose = QAction("Close Project", self)
        self.actionClose.triggered.connect(lambda: self.events.trigger_event(self.events.EventKeys.GUI_CLOSE_PROJECT))

        self.menuProject.addActions([self.actionOpen, self.actionClose])

        ## Seperator
        self.menuProject.addSeparator()

        ## Save
        self.actionSave = QAction("Save", self)
        self.actionSave.triggered.connect(lambda: self.events.trigger_event(self.events.EventKeys.GUI_SAVE_PRETEND))
        
        self.actionSaveAs = QAction("Save as...", self)
        self.actionSaveAs.triggered.connect(lambda: self.events.trigger_event(self.events.EventKeys.GUI_SAVE_PROJECT))

        self.menuProject.addActions([self.actionSave, self.actionSaveAs])

        ## Seperator
        self.menuProject.addSeparator()

        ## Settings / Info
        self.actionInfo = QAction("Info", self)

        self.menuProject.addActions([self.actionInfo])

        # The "Data" Tab
        self.menuData = QMenu("Data", self)

        self.actionPlot = QAction("Plot", self)
        self.actionPlot.triggered.connect(self.plotter_action)
        
        self.actionCalculation = QAction("Calculation", self)
        self.actionCalculation.triggered.connect(self.calculation_action)
        
        self.menuData.addAction(self.actionPlot)
        self.menuData.addAction(self.actionCalculation)
        
        # The Devices
        self.menuDevices = QMenu("Devices", self)
        
        self.actionDeviceCamera = QAction("Camera", self)
        self.actionDeviceCamera.triggered.connect(self.device_camera_action)
        
        self.actionDeviceMFC = QAction("MFC", self)
        self.actionDeviceMFC.triggered.connect(self.device_mfc_action)
        
        self.actionDevicePump = QAction("Pump", self)
        self.actionDevicePump.triggered.connect(self.device_pump_action)
        
        self.actionDeviceArduino = QAction("Arduino", self)
        self.actionDeviceArduino.triggered.connect(self.device_arduino_action)
        
        self.menuDevices.addAction(self.actionDeviceCamera)
        self.menuDevices.addAction(self.actionDeviceMFC)
        self.menuDevices.addAction(self.actionDevicePump)
        self.menuDevices.addAction(self.actionDeviceArduino)

        # The "Documentation"
        self.actionDocumentation = QAction("Documentation", self)

        self.addAction(self.menuProject.menuAction())
        self.addAction(self.menuData.menuAction())
        self.addAction(self.menuDevices.menuAction())
        self.addAction(self.actionDocumentation)

        self.menuMeasurement.setEnabled(False)
        self.live_view.setEnabled(False)
        self.actionClose.setEnabled(False)
        self.actionSave.setEnabled(False)
        self.actionSaveAs.setEnabled(False)
        
        self.menuData.setEnabled(False)

        return self
    
    def options_updater(self):
                
        if self.data.get_data(self.data.Keys.PROJECT_PATH, namespace=self.data.Namespaces.PROJECT_MANAGEMENT) is not None:
            state = False
            self.menuMixingTime.setEnabled(not state)
            self.menuMeasurement.setEnabled(not state)
            self.live_view.setEnabled(not state)
            self.actionClose.setEnabled(not state)
            self.actionSave.setEnabled(not state)
            self.actionSaveAs.setEnabled(not state)
            self.menuData.setEnabled(not state)
            self.actionSettings.setEnabled(not state)
            
        elif self.data.get_data(self.data.Keys.PROJECT_PATH, namespace=self.data.Namespaces.PROJECT_MANAGEMENT) is None:
            state = True
            self.menuMixingTime.setEnabled(not state)
            self.menuMeasurement.setEnabled(not state)
            self.live_view.setEnabled(not state)
            self.actionClose.setEnabled(not state)
            self.actionSave.setEnabled(not state)
            self.actionSaveAs.setEnabled(not state)
            self.menuData.setEnabled(not state)
            self.actionSettings.setEnabled(not state)

    def measurement_action(self):
        
        from view.main.mainframe import MainWindow
        from view.measurement_framework.measurement_framework import MeasurementFramework
        
        main_inst = MainWindow.get_instance()
        
        subwindows = main_inst.middle_layout.mdi_area.subWindowList()
        for subwindow in subwindows:
            if isinstance(subwindow.widget(), MeasurementFramework):
                QMessageBox.information(MainWindow.get_instance(), "Measurement Form", "There is already a measurement window open.")
                return
        
        measurementForm = MeasurementFramework()
        measurementForm.setupFramework()
        
        subwindow = QMdiSubWindow()
        subwindow.setWidget(measurementForm)
        subwindow.resize(900, 700)
        
        main_inst.middle_layout.mdi_area.addSubWindow(subwindow)
        
        subwindow.show()

    def project_setting(self):
        
        from view.main.mainframe import MainWindow
        from view.forms.settingForm.setting_form import SettingsForm
        
        main_inst = MainWindow.get_instance()
        
        subwindows = main_inst.middle_layout.mdi_area.subWindowList()
        for subwindow in subwindows:
            if isinstance(subwindow.widget(), SettingsForm):
                QMessageBox.information(MainWindow.get_instance(), "Settings Form", "There is already a setting window open.")
                return
        
        settingForm = SettingsForm()
        settingForm.setupForm()
        
        subwindow = QMdiSubWindow()
        subwindow.setWidget(settingForm)
        
        main_inst.middle_layout.mdi_area.addSubWindow(subwindow)
        
        subwindow.show()
        
    def calculation_action(self):
        
        from view.main.mainframe import MainWindow
        from view.forms.calculationForm.calcForm import CalculaionForm

        main_inst = MainWindow.get_instance()

        subwindows = main_inst.middle_layout.mdi_area.subWindowList()
        for subwindow in subwindows:
            if isinstance(subwindow.widget(), CalculaionForm):
                QMessageBox.information(MainWindow.get_instance(), "Plotter", "There is already a plotter open.")
                return
            
        userdata_db_path = os.path.join(self.data.get_data(self.data.Keys.PROJECT_FOLDER_USERDATA, namespace=self.data.Namespaces.PROJECT_MANAGEMENT), "userdata.db")

        query = """SELECT Name FROM MeasurementRegistry"""

        result = self.sql.read_or_write(userdata_db_path, query, "read")  # noqa: F841
        if not result:
            QMessageBox.information(MainWindow.get_instance(), "No measurements", "This project contains no measurements to plot.")
            return
        
        calculator = CalculaionForm()
        calculator.setupForm()

        subwindow = QMdiSubWindow()
        subwindow.setWidget(calculator)

        main_inst.middle_layout.mdi_area.addSubWindow(subwindow)

        subwindow.show()
    
    def plotter_action(self):

        from view.main.mainframe import MainWindow
        from view.forms.plotterForm.plotter_form import PlotterForm

        main_inst = MainWindow.get_instance()

        subwindows = main_inst.middle_layout.mdi_area.subWindowList()
        for subwindow in subwindows:
            if isinstance(subwindow.widget(), PlotterForm):
                QMessageBox.information(MainWindow.get_instance(), "Plotter", "There is already a plotter open.")
                return
            
        userdata_db_path = os.path.join(self.data.get_data(self.data.Keys.PROJECT_FOLDER_USERDATA, namespace=self.data.Namespaces.PROJECT_MANAGEMENT), "userdata.db")

        query = """SELECT Name FROM Measurementregistry"""

        result = self.sql.read_or_write(userdata_db_path, query, "read")  # noqa: F841
        if not result:
            QMessageBox.information(MainWindow.get_instance(), "No measurements", "This project contains no measurements to plot.")
            return

        plotter = PlotterForm()
        plotter.setupForm()

        subwindow = QMdiSubWindow()
        subwindow.setWidget(plotter)

        main_inst.middle_layout.mdi_area.addSubWindow(subwindow)

        subwindow.show()

    def live_view_action(self):

        # First we check if the camera is available
        try:
            if self.data.get_data(self.data.Keys.CAMERA, namespace=self.data.Namespaces.DEVICES) and not self.data.get_data(self.data.Keys.MEASUREMENT_RUNNING, namespace=self.data.Namespaces.MEASUREMENT):
                pass
            else:
                QMessageBox.warning(self, "Unable to open live view.",
                                "There is no camera connected or a measurement running. Please try again later.")
                return
        except Exception:
            QMessageBox.warning(self, "Unable to open live view.",
                                "There is no camera connected or a measurement running. Please try again later.")
            return

        from view.main.mainframe import MainWindow
        from view.liveviewForm.liveview_form import LiveViewForm

        main_inst = MainWindow.get_instance()

        subwindows = main_inst.middle_layout.mdi_area.subWindowList()
        for subwindow in subwindows:
            if isinstance(subwindow.widget(), LiveViewForm):
                QMessageBox.information(MainWindow.get_instance(), "Live View", "There is already a live view open.")
                return

        liveview = LiveViewForm()
        liveview.setupForm()

        subwindow = QMdiSubWindow()
        subwindow.setWidget(liveview)

        main_inst.middle_layout.mdi_area.addSubWindow(subwindow)

        subwindow.show()

    def single_image_analysis_action(self):
        
        from view.main.mainframe import MainWindow
        from view.single_image_analysis.single_image_analysis_form import SingleImageAnylsisForm
        
        main_inst = MainWindow.get_instance()

        single_image_form = SingleImageAnylsisForm()
        single_image_form.setupForm()
        
        subwindow = QMdiSubWindow()
        subwindow.setWidget(single_image_form)
        
        main_inst.middle_layout.mdi_area.addSubWindow(subwindow)
        
        subwindow.show()

    def device_camera_action(self):
        
        from view.main.mainframe import MainWindow
        from view.main.left_interactable.devices.dev_camera import UICameraWidget

        # First we check if the devices are even connected
        device = self.data.get_data(self.data.Keys.CAMERA, self.data.Namespaces.DEVICES)
        if not device:
            QMessageBox.information(MainWindow.get_instance(), "No Camera", "There is currently no Camera connected.")
            return

        main_inst = MainWindow.get_instance()

        subwindows = main_inst.middle_layout.mdi_area.subWindowList()
        for subwindow in subwindows:
            if isinstance(subwindow.widget(), UICameraWidget):
                QMessageBox.information(MainWindow.get_instance(), "Camera Settings", "There is already a camera settings window open.")
                return
            
        ui_camera = UICameraWidget()
        ui_camera.setupWidget()

        subwindow = QMdiSubWindow()
        subwindow.setWidget(ui_camera)

        main_inst.middle_layout.mdi_area.addSubWindow(subwindow)

        subwindow.show()

    def device_mfc_action(self):
        
        from view.main.mainframe import MainWindow
        from view.main.left_interactable.devices.dev_mfc import UIMFCWidget

        # First we check if the devices are even connected
        device = self.data.get_data(self.data.Keys.MFC, self.data.Namespaces.DEVICES)
        if not device:
            QMessageBox.information(MainWindow.get_instance(), "No MFC", "There is currently no massflow controller connected.")
            return

        main_inst = MainWindow.get_instance()

        subwindows = main_inst.middle_layout.mdi_area.subWindowList()
        for subwindow in subwindows:
            if isinstance(subwindow.widget(), UIMFCWidget):
                QMessageBox.information(MainWindow.get_instance(), "MFC Settings", "There is already a MFC settings window open.")
                return
        
        self.ui_mfc = UIMFCWidget()
        self.ui_mfc.setupWidget()

        subwindow = QMdiSubWindow()
        subwindow.setWidget(self.ui_mfc)

        main_inst.middle_layout.mdi_area.addSubWindow(subwindow)

        subwindow.show()

    def device_pump_action(self):
        
        from view.main.mainframe import MainWindow
        from view.main.left_interactable.devices.dev_pump import UIPumpWidget

        # First we check if the devices are even connected
        device = self.data.get_data(self.data.Keys.PUMP, self.data.Namespaces.DEVICES)
        if not device:
            QMessageBox.information(MainWindow.get_instance(), "No Pump", "There is currently no Pump connected.")
            return

        main_inst = MainWindow.get_instance()

        subwindows = main_inst.middle_layout.mdi_area.subWindowList()
        for subwindow in subwindows:
            if isinstance(subwindow.widget(), UIPumpWidget):
                QMessageBox.information(MainWindow.get_instance(), "Pump Settings", "There is already a Pump window open.")
                return
        
        self.ui_pump = UIPumpWidget()
        self.ui_pump.setupForm()

        subwindow = QMdiSubWindow()
        subwindow.setWidget(self.ui_pump)

        main_inst.middle_layout.mdi_area.addSubWindow(subwindow)

        subwindow.show()
        subwindow.resize(subwindow.size())

    def device_arduino_action(self):
        
        from view.main.mainframe import MainWindow
        from view.main.left_interactable.devices.dev_arduino import UIArduinoWidget

        # First we check if the devices are even connected
        device = self.data.get_data(self.data.Keys.ARDUINO, self.data.Namespaces.DEVICES)
        if not device:
            QMessageBox.information(MainWindow.get_instance(), "No Arduino", "There is currently no Arduino connected.")
            return

        main_inst = MainWindow.get_instance()

        subwindows = main_inst.middle_layout.mdi_area.subWindowList()
        for subwindow in subwindows:
            if isinstance(subwindow.widget(), UIArduinoWidget):
                QMessageBox.information(MainWindow.get_instance(), "Arduino Settings", "There is already a Pump window open.")
                return
        
        self.ui_pump = UIArduinoWidget()
        self.ui_pump.setupForm()

        subwindow = QMdiSubWindow()
        subwindow.setWidget(self.ui_pump)

        main_inst.middle_layout.mdi_area.addSubWindow(subwindow)

        subwindow.show()
        subwindow.resize(subwindow.size())

    def mixing_time_action(self):
        
        from view.main.mainframe import MainWindow
        from view.mixing_time_framework.mixing_time_frame import UIMixingTime

        # First we check if the devices are even connected
        device = self.data.get_data(self.data.Keys.PUMP, self.data.Namespaces.DEVICES)
        if not device:
            QMessageBox.information(MainWindow.get_instance(), "No Pump", "There is currently no Pump connected.")
            return

        main_inst = MainWindow.get_instance()

        subwindows = main_inst.middle_layout.mdi_area.subWindowList()
        for subwindow in subwindows:
            if isinstance(subwindow.widget(), UIMixingTime):
                QMessageBox.information(MainWindow.get_instance(), "Mixing Time", "There is already a Mixing Time window open.")
                return
        
        self.ui_pump = UIMixingTime()
        self.ui_pump.setupForm()

        subwindow = QMdiSubWindow()
        subwindow.setWidget(self.ui_pump)

        main_inst.middle_layout.mdi_area.addSubWindow(subwindow)

        subwindow.setWindowTitle("Mixing Time Measurement")
        subwindow.show()

    def closeEvent(self, event: QCloseEvent):
        
        try:
            self.timer.stop()
        except Exception:
            pass
        finally:
            event.accept()