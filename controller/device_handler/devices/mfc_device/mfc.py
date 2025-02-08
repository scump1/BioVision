
from sre_parse import State
import propar
import threading
from enum import Enum

from controller.device_handler.devices.mfc_device.states.all_states import HealthCheckState, SettingsSetter, PollingState, ReadMassFlowState, CloseValve, OpenValve
from controller.device_handler.devices.state_machine_template import Device

from operator_mod.logger.global_logger import Logger
from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from model.data.configuration_manager import ConfigurationManager

class MFC(Device):
    
    _instance = None
    _lock = threading.Lock()
    
    class States(Enum):
        HEALTH_CHECK_STATE = 1
        SETTING_SETTER_STATE = 2
        POLL_STATE = 3
        READ_MASSFLOW_STATE = 5
        CLOSE_VALVE = 6
        OPEN_VALVE = 7
            
    state_classes = {
        States.HEALTH_CHECK_STATE: HealthCheckState,
        States.SETTING_SETTER_STATE: SettingsSetter,
        States.POLL_STATE: PollingState,
        States.READ_MASSFLOW_STATE: ReadMassFlowState,
        States.OPEN_VALVE: OpenValve,
        States.CLOSE_VALVE: CloseValve
        # Add more states here
    }

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MFC, cls).__new__(cls)
        return cls._instance

    def __init__(self):
            
        super().__init__()

        # Utils
        self.configurations = ConfigurationManager.get_instance()
        self.logger = Logger("MFC").logger
        self.data = InMemoryData()
        
        self.mfc_instrument = None
        
        self._connect()
    
    def _connect(self):
        
        try:
            
            if self.mfc_instrument is None:
                self.mfc_instrument = propar.instrument('COM3')
 
            read = self.mfc_instrument.readParameter(205)

            if read is not None: # it might be 0.0 which means we need to check class not value
                self.data.add_data(self.data.Keys.MFC, True, namespace=self.data.Namespaces.DEVICES)
                
                # Get the config
                settings = self.configurations.get_configuration(self.configurations.Devices.MFC)  
                value = list(settings.values())
                
                self.mfc_instrument.writeParameter(206, value[0])
                self.logger.info("MFC operable.")
                
            else:
                self.data.add_data(self.data.Keys.MFC, False, namespace=self.data.Namespaces.DEVICES)
                self.logger.warning("Could not read parameter.")
        
        except Exception as e:
            self.data.add_data(self.data.Keys.MFC, False, namespace=self.data.Namespaces.DEVICES)
            self.logger.warning(f"Could not connect: {e}")
    
    @classmethod
    def get_instance(cls):
        return cls._instance