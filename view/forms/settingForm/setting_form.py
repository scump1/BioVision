
from PySide6.QtWidgets import QWidget, QTreeWidget, QTreeWidgetItem, QStackedWidget, QCheckBox, QComboBox, QSpinBox, QLabel, QHBoxLayout, QFormLayout, QFormLayout
from PySide6.QtGui import QCloseEvent

from operator_mod.in_mem_storage.in_memory_data import InMemoryData

class SettingsForm(QWidget):
    
    def __init__(self) -> None:
        
        super().__init__()
        
        self.data = InMemoryData()
        
        # Map for tree items and corresponding stacked widget indices
        self.page_map = {
            "Camera": 0,
            "Image Settings": 1,       # Maps to Camera's image settings
            "Arduino": 2,              # Placeholder for Arduino
            "Syringe Pump": 3,         # Placeholder for Syringe Pump
            "Mass Flow Controller": 4,  # Placeholder for Mass Flow Controller
            "About": 5                 # Placeholder for About
        }
        
    def setupForm(self):
        
        # Main layout
        self.main_layout = QHBoxLayout()
        
        # Leftside List Topic Selector
        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderLabel("Settings")
        
        # Items for device settings
        self.camera_item = QTreeWidgetItem(self.category_tree, ["Camera"])
        self.camera_item.addChild(QTreeWidgetItem(self.camera_item, ["Device Information"]))
        self.camera_item.addChild(QTreeWidgetItem(self.camera_item, ["Image Settings"]))
        
        self.arduino_item = QTreeWidgetItem(self.category_tree, ["Arduino"])
        self.arduino_item.addChild(QTreeWidgetItem(self.arduino_item, ["Device Information"]))

        self.pump_item = QTreeWidgetItem(self.category_tree, ["Syringe Pump"])
        self.pump_item.addChild(QTreeWidgetItem(self.pump_item, ["Device Information"]))
        
        self.mfc_item = QTreeWidgetItem(self.category_tree, ["Mass Flow Controller"])
        self.mfc_item.addChild(QTreeWidgetItem(self.mfc_item, ["Device Information"]))
        
        self.software_item = QTreeWidgetItem(self.category_tree, ["About"])
        
        self.category_tree.itemClicked.connect(self.change_page)
        
        # Stacked Widget
        self.settings_widget = QStackedWidget()
        
        dev_inf_widget, img_widget = self.create_camera_pages()
        self.settings_widget.addWidget(dev_inf_widget)
        self.settings_widget.addWidget(img_widget)
        
        arduino_widget = self.arduino_page()
        self.settings_widget.addWidget(arduino_widget)
        
        syringe_pump = self.syringe_pump_page()
        self.settings_widget.addWidget(syringe_pump)
        
        mfc_widget = self.mfc_page()
        self.settings_widget.addWidget(mfc_widget)
        
        about_widget = self.about_page()
        self.settings_widget.addWidget(about_widget)
        
        # At the end
        self.main_layout.addWidget(self.category_tree)
        self.main_layout.addWidget(self.settings_widget)
        self.setLayout(self.main_layout)
        
    def create_camera_pages(self) -> list:
        """Returns two widgets for the camera settings."""
        
        dev_inf_widget = QWidget()
        dev_inf_layout = QFormLayout()
        
        dev_inf_layout.addRow("Name:", QLabel("Daheng Imaging MERCK2-1200"))
        dev_inf_layout.addRow("Serial Number", QLabel("FCU23120403"))
        
        dev_inf_widget.setLayout(dev_inf_layout)
        
        img_widget = QWidget()
        img_layout = QFormLayout()

        img_layout.addRow("Resolution", QLabel("4096 x 3072"))
                               
        img_depth = QComboBox()
        img_depth.addItems(["8-bit", "12-bit"])

        img_color_check = QCheckBox()
        img_color_check.setChecked(True)
        img_color_check.stateChanged.connect(lambda state: img_depth.setEnabled(state != 0))
        img_layout.addRow("Color Images", img_color_check)
        img_layout.addRow("Color Depth", img_depth)
        
        img_exposuretime = QSpinBox()
        img_exposuretime.setMinimum(10)
        img_exposuretime.setMaximum(3000)
        img_layout.addRow("Exposure Time (ms):", img_exposuretime)
        
        img_widget.setLayout(img_layout)
        
        return dev_inf_widget, img_widget
        
    def arduino_page(self) -> QWidget:
        
        widget = QWidget()
        arduino_layout = QFormLayout()
        
        arduino_layout.addRow("Model:", QLabel("Arduino Uno R2"))
        arduino_layout.addRow("Port:", QLabel("COM3"))
        
        widget.setLayout(arduino_layout)
        return widget
    
    def syringe_pump_page(self) -> QWidget:
        
        widget = QWidget()
        syringe_pump_layout = QFormLayout()
        
        syringe_pump_layout.addRow("Model:", QLabel("CETONI Nemesys Base 120"))
        syringe_pump_layout.addRow("Port:", QLabel("COM4"))
        
        widget.setLayout(syringe_pump_layout)
        return widget
    
    def mfc_page(self) -> QWidget:
        
        widget = QWidget()
        mfc_layout = QFormLayout()
        
        mfc_layout.addRow("Model:", QLabel("Bronkhorst XDD"))
        mfc_layout.addRow("Port:", QLabel("COM5"))
        
        widget.setLayout(mfc_layout)
        return widget 
        
    def about_page(self) -> QWidget:
        
        widget = QWidget()
        about_layout = QFormLayout()
        
        about_layout.addRow("License:", QLabel("MIT License"))
        about_layout.addRow("Version:", QLabel("0.4.1"))
        
        about_layout.addRow("Developer:", QLabel("Leon Pastwa"))
        about_layout.addRow("Email:", QLabel("l.pastwa@tu-braunschweig.de"))
        
        widget.setLayout(about_layout)
        return widget
        
    def change_page(self, item):
        if item:
            item_text = item.text(0)  # Get the name of the item
            
            # If the clicked item is "Device Information", retrieve the parent's text
            if item_text == "Device Information":
                parent = item.parent()
                if parent:
                    item_text = parent.text(0)

            # Lookup the index in the page_map
            index = self.page_map.get(item_text)
            if index is not None:
                self.settings_widget.setCurrentIndex(index)
                
    def closeEvent(self, event: QCloseEvent):
        
        try:
            from view.main.mainframe import MainWindow
            instance = MainWindow.get_instance()
            
            subwindows = instance.middle_layout.mdi_area.subWindowList()
            
            for subwindow in subwindows:
                widget = subwindow.widget()
                if isinstance(widget, SettingsForm):
                    instance.middle_layout.mdi_area.removeSubWindow(subwindow)
            
        finally:
            event.accept()