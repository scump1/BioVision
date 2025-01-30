
from enum import Enum
import threading

from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from operator_mod.eventbus.event_handler import EventManager
from operator_mod.logger.global_logger import Logger

from controller.device_handler.devices.arduino_device.arduino import Arduino
from controller.device_handler.devices.camera_device.camera import Camera
from controller.device_handler.devices.mfc_device.mfc import MFC
from controller.device_handler.devices.pump_device.pump import Pump

from controller.device_handler.device_handler_class.states.all_states import HealthCheckState
from controller.device_handler.devices.state_machine_template import Device

class DeviceHandler(Device):

    _instance = None
    _lock = threading.Lock()
    
    class States(Enum):
        HEALTH_CHECK_STATE = 1
    
    state_classes = {
        States.HEALTH_CHECK_STATE: HealthCheckState
        # Add more states here
    }

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DeviceHandler, cls).__new__(cls)
                return cls._instance

    def __init__(self):

        super().__init__()

        self.data = InMemoryData()
        self.events = EventManager()
        self.logger = Logger("Controller").logger
                    
        self.startup_devices()
    
        self.data.add_data(self.data.Keys.MEASUREMENT_RUNNING, False, namespace=self.data.Namespaces.MEASUREMENT)
    
        self.data.add_data(self.data.Keys.CAMERA, False, namespace=self.data.Namespaces.DEVICES)
        self.data.add_data(self.data.Keys.ARDUINO, False, namespace=self.data.Namespaces.DEVICES)
        self.data.add_data(self.data.Keys.MFC, False, namespace=self.data.Namespaces.DEVICES)
        self.data.add_data(self.data.Keys.PUMP, False, namespace=self.data.Namespaces.DEVICES)
        
        self.add_task(self.States.HEALTH_CHECK_STATE, 0)

    def startup_devices(self):
        
        # Devices are not changing, these register a healthcheck event; Both threads are deamon on init
        self.arduino = Arduino()
        self.camera = Camera()
        self.mfc = MFC()
        self.pump = Pump()
        
        # Device linked dict
        self.devices = {
            "Arduino" : [self.data.Keys.ARDUINO, self.arduino],
            "Camera" : [self.data.Keys.CAMERA, self.camera],
            "MFC": [self.data.Keys.MFC, self.mfc],
            "Pump": [self.data.Keys.PUMP, self.pump]
        }
    
    @classmethod
    def get_instance(cls):
        return cls._instance