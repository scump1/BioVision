
import datetime
import time
from abc import ABC, abstractmethod

from operator_mod.logger.global_logger import Logger
from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from model.utils.resource_manager import ResourceManager
from controller.algorithms.data_writer.data_writer import DataWriter

# Abstract State Class
class State(ABC):
    
    def __init__(self, device, runtime):
        
        self.logger = Logger("Arduino").logger
        self.data = InMemoryData()
        self.data_writer = DataWriter()
        self.namespace = "Arduino"
        self.res_man = ResourceManager()
        
        # Live Data Recording+
        self.live_recording = False
        
        # Some other states
        self.valve_state = False
        
        self.device = device
        self.runtime_target = datetime.datetime.now() + datetime.timedelta(seconds=runtime)
        self.terminated = False

    def run(self):
        try:
            self.run_logic()
        except Exception as e:
            self.logger.warning(f"State execution failed: {e}")
        finally:
            self.logger.info("Finished a State.")
            self.device.task_free.set()
            
    @abstractmethod
    def run_logic(self):
        pass

    def _wait_for_response(self, expected_response=None, timeout=5):

        start_time = time.time()
        response = None
        
        while time.time() - start_time < timeout:
            if self.device.serial_con.in_waiting > 0:
                response = self.device.serial_con.readline().decode().strip()
                
                if response is not None:
                    break
                
            if timeout > start_time:
                self.logger.warning("Timeout condition reached.")
                return False
                
        if expected_response is not None:
            
            expected_type = type(expected_response)
            response = expected_type(response)
        
            if expected_response == response:
                return True
            return False
        
        elif response == "Y":
            return True
        return False

    def terminate(self):
        self.terminated = True
        