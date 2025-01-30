
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from operator_mod.eventbus.event_handler import EventManager

from view.measurement_framework.managers.slot_items.slotitem import SlotItemWidget
from model.measurements.routine_system.routine_system import RoutineSystem

class SlotManager(QWidget):
    
    def __init__(self, routinesystem: RoutineSystem) -> None:
        
        super().__init__()
        
        self.events = EventManager()
        self.events.add_listener(self.events.EventKeys.UPDATE_TO_TOPMOST_SLOT, self._update_to_topmost_slot, 0, True)

        # The uid connects to the instance of RoutineSystem
        self.routine = routinesystem
    
    def setupWidget(self):
        
        mainlayout = QVBoxLayout()
        mainlayout.setContentsMargins(5,5,5,5)
        
        # Buttons
        buttons = QHBoxLayout()
        add = QPushButton("Add")
        add.pressed.connect(self.add_item)
        delete = QPushButton("Del")
        delete.pressed.connect(self.delete_item)

        buttons.addWidget(add)
        buttons.addWidget(delete)
        
        self.slot_list = QListWidget()
        self.slot_list.currentItemChanged.connect(self._current_item_changed)
        
        mainlayout.addLayout(buttons)
        mainlayout.addWidget(self.slot_list)
        
        self.setLayout(mainlayout)
    
    def clear_all_slots(self):
        
        if self.slot_list.count() == 0:
            return 
        
        while self.slot_list.count() > 0:
            
            item = self.slot_list.item(0)
            
            if item:
                widget = self.slot_list.itemWidget(item)
                slot = widget.slot
                
                self.events.trigger_event(self.events.EventKeys.DELETE_SLOT_LIST, slot)
                
                self.routine.delete_slot(slot.uid) 
                
                row = self.slot_list.row(item)
                self.slot_list.takeItem(row)
    
    def _update_to_topmost_slot(self):
        
        item = self.slot_list.item(0)
        
        if item:
            widget = self.slot_list.itemWidget(item)
            slot = widget.slot
            
            self.events.trigger_event(self.events.EventKeys.CURRENT_SLOT_CHANGED, slot)
                
    
    def slot_setter(self, slot_settings):

        name, runtime, unit, _, interaction = slot_settings
        newslot = self.routine.create_slot(name, runtime)

        widget = SlotItemWidget(newslot, self.routine)
        widget.name_edit.setText(name)
        widget.runtime_value.setValue(runtime)
        widget.runtime_unit.setCurrentText(unit)
        
        if interaction:
            widget.stopwait.setChecked(True)
        
        listItem = QListWidgetItem()
        listItem.setSizeHint(widget.sizeHint())
        
        self.slot_list.addItem(listItem)
        self.slot_list.setItemWidget(listItem, widget)
        
        self.events.trigger_event(self.events.EventKeys.NEW_SLOT_LIST, newslot)
        
    def add_item(self):
        
        # We create the slot in the routinesystem
        slot = self.routine.create_slot('Slot', 60)
        
        # First we create the widget
        widget = SlotItemWidget(slot, self.routine)
        listItem = QListWidgetItem()
        listItem.setSizeHint(widget.sizeHint())
        
        self.slot_list.addItem(listItem)
        self.slot_list.setItemWidget(listItem, widget)
        
        self.events.trigger_event(self.events.EventKeys.NEW_SLOT_LIST, slot)
        
    def _current_item_changed(self):
        item = self.slot_list.currentItem()
        
        if item:
            widget = self.slot_list.itemWidget(item)
            
            self.events.trigger_event(self.events.EventKeys.CURRENT_SLOT_CHANGED, widget.slot)
                
    def delete_item(self):
        
        item = self.slot_list.currentItem()
        
        if item:
                        
            widget = self.slot_list.itemWidget(item)
            slot = widget.slot
            self.events.trigger_event(self.events.EventKeys.DELETE_SLOT_LIST, slot)

            self.routine.delete_slot(widget.slot.uid) 

            row = self.slot_list.row(item)
            self.slot_list.takeItem(row)
            
            