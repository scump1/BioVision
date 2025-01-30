
import datetime
from abc import ABC, abstractmethod

from operator_mod.logger.global_logger import Logger
from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from model.utils.resource_manager import ResourceManager
from operator_mod.eventbus.event_handler import EventManager

# Abstract State Class
class State(ABC):
    
    def __init__(self, device, runtime):
        
        self.logger = Logger("Camera").logger
        self.data = InMemoryData()
        self.namespace = self.data.Namespaces.CAMERA
        self.res_man = ResourceManager()
        self.events = EventManager()
        
        self.device = device
        self.runtime_target = datetime.datetime.now() + datetime.timedelta(seconds=runtime)
        self.terminated = False

    def run(self):
        try:
            self.run_logic()
        except Exception as e:
            self.logger.warning(f"Error in camera state: {e}.")
        finally:
            self.logger.info("Finished a state.")
            self.device.task_free.set()

    @abstractmethod
    def run_logic(self):
        pass

    def terminate(self):
        self.terminated = True
        