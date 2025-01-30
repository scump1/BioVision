
import datetime
from abc import ABC, abstractmethod

from operator_mod.logger.global_logger import Logger
from operator_mod.in_mem_storage.in_memory_data import InMemoryData

from controller.algorithms.data_writer.data_writer import DataWriter

# Abstract State Class
class State(ABC):
    
    def __init__(self, device, runtime):
        
        self.logger = Logger("Pump").logger
        self.data = InMemoryData()
        
        self.device = device
        self.runtime_target = datetime.datetime.now() + datetime.timedelta(seconds=runtime)
        self.terminated = False

    def run(self):
        try:
            self.run_logic()
        except Exception as e:
            self.logger.warning(f"Error in Pump State: {e}.")
        finally:
            self.logger.info("Finished State.")
            self.device.task_free.set()

    @abstractmethod
    def run_logic(self):
        pass

    def terminate(self):
        self.terminated = True