
from model.model import Model
from controller.controller import Controller
from view.start_gui import GUInterface
from operator_mod.operator_mod import OperatorModerator

from operator_mod.eventbus.event_handler import EventManager

from controller.device_handler.devices.camera_device.camera import Camera
from controller.device_handler.devices.arduino_device.arduino import Arduino
from controller.device_handler.devices.mfc_device.mfc import MFC
from controller.device_handler.devices.pump_device.pump import Pump

class ApplicationCoordinator:

    _instance = None

    def __new__(cls):

        if cls._instance is None:
            cls._instance = super(ApplicationCoordinator, cls).__new__(cls)
        return cls._instance

    def __init__(self):

        # Starts the controller parts: EventBus, InMemDataStore and more
        self.startup()

    def startup(self):

        self.model = Model()
        self.model.start_model()

        self.controller = Controller()
        self.controller.start_controller()

        ope = OperatorModerator()
        ope.start_operator()
        
        # At last we register the Events
        self.events = EventManager.get_instance()
        self.events.add_listener(self.events.EventKeys.APPLICATION_SHUTDOWN, self.shutdown, 0)
        
        # Start the GUI
        self.gui = GUInterface()
        self.gui.start_gui()

    def shutdown(self):
                
        # Shutdown parts
        self.controller.shutdown()
        
        # Shutdown devices
        cam = Camera.get_instance()
        cam.shutdown()
        
        ard = Arduino.get_instance()
        ard.shutdown()
        
        mfc = MFC.get_instance()
        mfc.shutdown()
        
        pump = Pump.get_instance()
        pump.shutdown()
        
        # Last end the GUI cycle
        self.gui.shutdown()

if __name__ == "__main__":

    Appcoor = ApplicationCoordinator()