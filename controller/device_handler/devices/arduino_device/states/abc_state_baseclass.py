
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
            
            if type(expected_response) == float:
                # we need to check for floating point errors and stuff
                if abs(expected_response - float(response)) < 1e-5:
                    return True
                else:
                    self.logger.warning(f"Discrepancy between response: {response} and expected response: {expected_response}.")
                    return False
            
            elif response == expected_response:
                return True
            
            else:
                self.logger.warning(f"Discrepancy between response: {response} and expected response: {expected_response}.")
                return False
        
        elif response == "Y":
            return True
        return False

    def terminate(self):
        self.terminated = True
        