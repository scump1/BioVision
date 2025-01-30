
import datetime
from abc import ABC, abstractmethod

from operator_mod.logger.global_logger import Logger
from operator_mod.in_mem_storage.in_memory_data import InMemoryData

# Abstract State Class
class State(ABC):
    
    def __init__(self, device_handler, runtime):
        
        self.logger = Logger("Controller").logger
        self.data = InMemoryData()
        
        self.device_handler = device_handler
        self.runtime_target = datetime.datetime.now() + datetime.timedelta(seconds=runtime)
        self.terminated = False

    def run(self):
        try:
            self.run_logic()
        except Exception as e:
            self.logger.warning(f"Error occured: {e}.")
        finally:
            self.device_handler.current_state = None
            self.logger.info("Finished a state.")

    @abstractmethod
    def run_logic(self):
        pass

    def terminate(self):
        self.terminated = True