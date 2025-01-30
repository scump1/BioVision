
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

import re

from operator_mod.eventbus.event_handler import EventManager
from model.measurements.routine_system.routine_system import RoutineSystem
from model.projects.profile_manager import ProfileManager

class ProfileWidget(QWidget):
    
    def __init__(self, routinesystem: RoutineSystem):
        
        super().__init__()
        
        self.events = EventManager()
        
        self.profiles = ProfileManager()
        self.old_profiles = None
        
        # Timer for profile updateing
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.available_profiles_updater)
        
        self.routine = routinesystem
        
    def setupWidget(self):
        
        # Settings
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # main
        self.mainlayout = QVBoxLayout()
        self.mainlayout.setDirection(QVBoxLayout.Direction.TopToBottom)
        
        ### profile loading
        profile_loader = QVBoxLayout()
        
        profile_load_label = QLabel("Load a profile")
        
        self.profile_load_selector = QComboBox()
        
        self.profile_load_button = QPushButton("Load Profile")
        self.profile_load_button.pressed.connect(self.load_profile)
        
        profile_loader.addWidget(profile_load_label)
        profile_loader.addWidget(self.profile_load_selector)
        profile_loader.addWidget(self.profile_load_button)
        
        ### profile deleting
        profile_deleter = QVBoxLayout()
        
        profile_deleter_label = QLabel("Delete a profile")
        
        self.profile_deleter_selector = QComboBox()
        
        self.profile_deleter_button = QPushButton("Delete Profile")
        self.profile_deleter_button.pressed.connect(self.delete_profile)
        
        profile_deleter.addWidget(profile_deleter_label)
        profile_deleter.addWidget(self.profile_deleter_selector)
        profile_deleter.addWidget(self.profile_deleter_button)
        
        ### profile creator
        profile_creator = QVBoxLayout()
        
        profile_creator_label = QLabel("Save as profile")
        
        self.profile_creator_name = QLineEdit()
        
        profile_creator_saver = QPushButton("Save Profile")
        profile_creator_saver.pressed.connect(self.save_profile)
        
        profile_creator.addWidget(profile_creator_label)
        profile_creator.addWidget(self.profile_creator_name)
        profile_creator.addWidget(profile_creator_saver)
        
        spacer = QSpacerItem(20,20)
        
        self.mainlayout.addLayout(profile_loader)
        self.mainlayout.addItem(spacer)
        self.mainlayout.addLayout(profile_deleter)
        self.mainlayout.addItem(spacer)
        self.mainlayout.addLayout(profile_creator)
        
        self.setLayout(self.mainlayout)
        
        # Start the timer
        self.timer.start()
        
    def save_profile(self):
        
        name = self.profile_creator_name.text()
        
        if not name:
            from view.main.mainframe import MainWindow
            QMessageBox.information(MainWindow.get_instance(), "Profile Name", "Please enter a valid profile name.", QMessageBox.StandardButton.Ok)
            return
        
        # Name and Data
        name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', name)
        slots = self.routine.slots
        
        self.profiles.save_profile(name, slots)
        
    def available_profiles_updater(self):
        
        profiles = self.profiles.list_profiles()
        
        if len(profiles) == 0:
            self.profile_load_selector.setEnabled(False)
            self.profile_load_button.setEnabled(False)
            self.profile_deleter_selector.setEnabled(False)
            self.profile_deleter_button.setEnabled(False)
        
        else:
            self.profile_load_selector.setEnabled(True)
            self.profile_load_button.setEnabled(True)
            self.profile_deleter_selector.setEnabled(True)
            self.profile_deleter_button.setEnabled(True)
        
        if profiles != self.old_profiles:
            
            self.profile_load_selector.clear()
            self.profile_deleter_selector.clear()
            
            self.profile_load_selector.addItems(profiles)
            self.profile_deleter_selector.addItems(profiles)
            
            self.old_profiles = profiles
            
    def delete_profile(self):
        
        name = self.profile_deleter_selector.currentText()
        if name:
            from view.main.mainframe import MainWindow
            result = QMessageBox.warning(MainWindow.get_instance(), "Delete Profile", f"Do you really want to delete the profile: {name}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            
            if result == QMessageBox.StandardButton.Yes:
                self.profiles.delete_profile(name)
            else: 
                return
            
    def load_profile(self):
        
        name = self.profile_load_selector.currentText()
        
        if name:
            data = self.profiles.load_profile(name)
            self.events.trigger_event(self.events.EventKeys.PROFILE_SETTER, data)
               
    def closeEvent(self, event: QCloseEvent):
        
        try:
            
            if self.timer.isActive():
                self.timer.stop()
                
        finally:
            event.accept()