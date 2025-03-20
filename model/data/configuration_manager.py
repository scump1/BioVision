
from enum import Enum
import os
import threading

from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from operator_mod.eventbus.event_handler import EventManager

from model.utils.file_access.file_access_manager import FileAccessManager
from model.utils.JSON.json_manager import JSONManager
from operator_mod.logger.global_logger import Logger

class ConfigurationManager:
    
    """Manages device and application configurations. Project specific configurations possible. 
    """
    
    _instance = None
    _lock = threading.Lock()
        
    class Devices(Enum):
        CAMERA = "Camera"
        MFC = "MFC"
        PUMP = "Pump"
        
    class CameraSettings(Enum):
        AUTOWHITE = 1
        EXPOSURETIME = 2
        GAIN = 3
        SATURATION = 4
    
    class MFCSettings(Enum):
        MASSFLOW = 1
    
    class PumpSettings(Enum):
        SYRINGE_DIAMETER = 1
        SYRINGE_LENGTH = 2
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ConfigurationManager, cls).__new__(cls)
            cls._instance.configurations = {ConfigurationManager.Devices.CAMERA: None , ConfigurationManager.Devices.MFC: None, ConfigurationManager.Devices.PUMP: None}
        return cls._instance
    
    def __init__(self):

        # Utils
        self.data = InMemoryData()
        self.json = JSONManager()
        self.logger = Logger("Application").logger
        self.fam = FileAccessManager()
        
        self.events = EventManager.get_instance()
        
        # Settings
        # This is a list in form : autowhite_balance, exposuretime, gain, saturation = settings
        self.camera_standard = {
            ConfigurationManager.CameraSettings.AUTOWHITE: 1, 
            ConfigurationManager.CameraSettings.EXPOSURETIME: 150, 
            ConfigurationManager.CameraSettings.GAIN: 20, 
            ConfigurationManager.CameraSettings.SATURATION: 0
            }
        
        # MFC Standard : massflow = settings
        self.mfc_standard = {ConfigurationManager.MFCSettings.MASSFLOW: 10}
        
        self.pump_standard = {
            ConfigurationManager.PumpSettings.SYRINGE_DIAMETER: 7.976,
            ConfigurationManager.PumpSettings.SYRINGE_LENGTH: 50}
        
        self._create_standard_settings()
        
    def _create_standard_settings(self) -> None:
        """Creates the standard settings.
        """
        if self.configurations[ConfigurationManager.Devices.CAMERA] is None:
            self.configurations[ConfigurationManager.Devices.CAMERA] = self.camera_standard
            
        if self.configurations[ConfigurationManager.Devices.MFC] is None:
            self.configurations[ConfigurationManager.Devices.MFC] = self.mfc_standard
    
        if self.configurations[ConfigurationManager.Devices.PUMP] is None:
            self.configurations[ConfigurationManager.Devices.PUMP] = self.pump_standard
    
    def get_configuration(self, device: Devices) -> dict:
        """Return the configuration dictionary for a device.

        Args:
            device (Devices): CAMERA or MFC

        Returns:
            dict: A dictionary of settings for the device
        """
        with self._lock:
            return self.configurations.get(device, {}).copy() if device in self.configurations else None
        
    def change_configuration(self, device: Enum, setting: Enum, value: int | float) -> None:
        """Change one specific setting of a configuration.

        Args:
            device (Enum): CAMERA or MFC
            setting (Enum): Any setting
            value (any): Mostly (int)

        Returns:
            None: No return
        """
        with self._lock:
            if device in self.configurations:
                config = self.configurations[device]
                if setting in config and isinstance(value, (int, float)):
                    config[setting] = value

                    # Automatically saving the config
                    self._save_configuration()
                    
                else:
                    self.logger.warning(f"Setting {setting} not in device {device}.")
            
            else:
                self.logger.warning(f"Device {device} not in Configurations.")
                
    def _save_configuration(self) -> None:
        """Saves the current configuration to a JSON file."""
        
        path = self.data.get_data(self.data.Keys.PROJECT_FOLDER_USERDATA, self.data.Namespaces.PROJECT_MANAGEMENT)
        
        try:
            # Serialize Enum keys for JSON storage
            serializable_config = {
                device.value: {setting.name: value for setting, value in config.items()}
                for device, config in self.configurations.items()
            }
            self.json.write_json(serializable_config, path, "device_configuration", True)
            self.logger.info(f"Configuration saved to {path}.")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            
    def load_configuration(self) -> None:
        """Loads the configuration from a JSON file."""
        path = self.data.get_data(self.data.Keys.PROJECT_FOLDER_USERDATA, self.data.Namespaces.PROJECT_MANAGEMENT)
        
        with self._lock:
            try:
                filepath = os.path.join(path, 'device_configuration.json')
                if os.path.exists(filepath):
                    config_data = self.json.load_json(filepath)
                  
                    config_data = dict(config_data[0])
                  
                    loaded_config = {}
                    
                    for device, settings in config_data.items():
                        loaded_config[ConfigurationManager.Devices(device)] = {}
                    
                        for setting, value in settings.items():
                            
                            if hasattr(ConfigurationManager.CameraSettings, setting):
                                loaded_config[ConfigurationManager.Devices(device)][getattr(ConfigurationManager.CameraSettings, setting)] = value
                    
                            elif hasattr(ConfigurationManager.MFCSettings, setting):
                                loaded_config[ConfigurationManager.Devices(device)][getattr(ConfigurationManager.MFCSettings, setting)] = value
                                
                            elif hasattr(ConfigurationManager.PumpSettings, setting):
                                loaded_config[ConfigurationManager.Devices(device)][getattr(ConfigurationManager.PumpSettings, setting)] = value

                    self.configurations.update(loaded_config)
                    self._apply_condigurations()
                    
                    self.logger.info("Configuration loaded successfully.")
                else:
                    self.logger.error(f"Invalid path: {filepath}")
            except Exception as e:
                self.logger.error(f"Failed to load configuration: {e}")
    
    def _apply_condigurations(self):
    
        self.events.trigger_event(self.events.EventKeys.CONFIGURATION_SETTER_PUMP)
        self.events.trigger_event(self.events.EventKeys.CONFIGURATION_SETTER_MFC)
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance