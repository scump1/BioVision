
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from operator_mod.eventbus.event_handler import EventManager
from view.measurement_framework.managers.setting_items.camera_item import CameraItemWidget
from view.measurement_framework.managers.setting_items.algorithm_item import AlgorithmItemWidget
from view.measurement_framework.managers.setting_items.mfc_item import MFCItemWidget
from view.measurement_framework.managers.setting_items.environment_item import EnvironmentItemWidget

from model.measurements.routine_system.routine_system import RoutineSystem, RoutineData

class SettingsManager(QWidget):
    
    def __init__(self, routinesystem) -> None:
        
        super().__init__()
        
        self.events = EventManager()
        self.events.add_listener(self.events.EventKeys.CURRENT_SLOT_CHANGED, self.update_current_slot, 0, True)
        self.events.add_listener(self.events.EventKeys.NEW_SLOT_LIST, self.add_settings_list, 0, True)
        self.events.add_listener(self.events.EventKeys.DELETE_SLOT_LIST, self.delete_settings_list, 0, True)
        
        self.routinesystem = routinesystem
        self.current_slot = None
        
        # The possible Items to add
        self.addables = {
            "Camera": CameraItemWidget,
            "Algorithm": AlgorithmItemWidget,
            "MFC": MFCItemWidget,
            "Environment": EnvironmentItemWidget
        }
        
        # Keeps track of the slotpages as: dict = {slot.uid: list_widget}
        self.slot_pages = {}
    
    def setupWidget(self):
        
        mainlayout = QVBoxLayout()
        
        # Buttons
        buttons = QHBoxLayout()
        add = QPushButton("Add")
        add.pressed.connect(self.add_settings_item)
        
        delete = QPushButton("Delete")
        delete.pressed.connect(self.delete_settings_item)
                
        self.setting = QComboBox()
        self.setting.addItems(["Algorithm", "Camera", "Environment", "MFC"])
        
        buttons.addWidget(self.setting)
        buttons.addWidget(add)
        buttons.addWidget(delete)
        
        self.stacked_widget = QStackedWidget()
        
        # Current Slot Label
        self.current_slot_label = QLabel()
        
        mainlayout.addLayout(buttons)
        mainlayout.addWidget(self.current_slot_label)
        mainlayout.addWidget(self.stacked_widget)
        
        self.setLayout(mainlayout)
    
    def settings_setter(self, setting):
        
        if setting.name == RoutineData.Parameter.TEMPERATURE:
            widget = self.addables["Environment"](self.routinesystem, self.current_slot)
            widget.temp_value.setValue(setting.setting.target)
            
        elif setting.name == RoutineData.Parameter.ALGORITHMS:
            widget = self.addables["Algorithm"](self.routinesystem, self.current_slot)
            widget.algorithms.setCurrentText(setting.setting.algorithm)
            
        elif setting.name == RoutineData.Parameter.CAMERA:
            widget = self.addables["Camera"](self.routinesystem, self.current_slot)
            widget.img_count.setValue(setting.setting.img_count)
            time, unit = self.runtime_converter(setting.setting.interval)
            widget.interval_count.setValue(time)
            widget.interval_time_unit.setCurrentText(unit)
            
        elif setting.name == RoutineData.Parameter.MFC:
            widget = self.addables["MFC"](self.routinesystem, self.current_slot)
            widget.mfc_value.setValue(setting.setting.massflow)
            
        else:
            return
        
        listwidget = self.slot_pages[self.current_slot.uid]
        listItem = QListWidgetItem()
        listItem.setSizeHint(widget.sizeHint())
        
        listwidget.addItem(listItem)
        listwidget.setItemWidget(listItem, widget)
    
    def runtime_converter(self, settingstime):
        """Converts the runtime in seconds into a sensible unit format"""
        if settingstime > 3600:
            runtime = settingstime / 3600
            unit = 'h'
        elif settingstime > 60:
            runtime = settingstime / 60
            unit = 'min'
        else:
            runtime = settingstime
            unit = 's'
        
        return runtime, unit
    
    def add_settings_item(self):
        
        listwidget = self.slot_pages[self.current_slot.uid]
        
        # First we create the widget
        widget = self.addables[self.setting.currentText()](self.routinesystem, self.current_slot)
        listItem = QListWidgetItem()
        listItem.setSizeHint(widget.sizeHint())
        
        exists_already = False
        for i in range(listwidget.count()):
            existing_widget = listwidget.itemWidget(listwidget.item(i))
                            
            if existing_widget and type(existing_widget) == type(widget):
                exists_already = True
                break
        
        if not exists_already:
            listwidget.addItem(listItem)
            listwidget.setItemWidget(listItem, widget)
    
    def delete_settings_item(self):
        
        listwidget = self.slot_pages[self.current_slot.uid]
        item = listwidget.currentItem()
        
        if item:
            widget = listwidget.itemWidget(item)
            widget.remove_setting()
            
            row = listwidget.row(item)
            listwidget.takeItem(row)
        
    def add_settings_list(self, slot):
            
        self.settings_list = QListWidget()

        self.slot_pages[slot.uid] = self.settings_list
        self.stacked_widget.addWidget(self.settings_list)
        
        self.update_current_slot(slot)
        
    def update_current_slot(self, slot):
        
        self.current_slot = slot
        self.current_slot_label.setText(f'Selected Slot: {slot.name}')
        
        index = self.stacked_widget.indexOf(self.slot_pages[slot.uid])
        self.stacked_widget.setCurrentIndex(index)
        
    def delete_settings_list(self, slot):
        
        widget = self.slot_pages.get(slot.uid, None)
        
        if widget is not None:

            while widget.count() > 0:
                
                item = widget.item(0)
                if item:
                    
                    itemwidget = widget.itemWidget(item)
                    itemwidget.remove_setting()
                    
                    row = widget.row(item)
                    widget.takeItem(row)
            
            self.stacked_widget.removeWidget(widget)
            self.events.trigger_event(self.events.EventKeys.UPDATE_TO_TOPMOST_SLOT)
            
    def wipe_all_lists(self):
        
        for widget in self.slot_pages.values():
            
            item = widget.item(0)
            if item:
                
                itemwidget = widget.itemWidget(item)
                itemwidget.remove_setting()
                
                row = widget.row(item)
                widget.takeItem(row)
            
            self.stacked_widget.removeWidget(widget)