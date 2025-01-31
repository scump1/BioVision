

from controller.device_handler.devices.camera_device.camera import Camera

from operator_mod.measurements.measurement_runner.mixing_time_runner import MixingTimeRunner
from model.measurements.mixing_time_creator import MixingTimeCreator

class MixingTimeHandler:
    
    def __init__(self):
        
        self.camera = Camera.get_instance()
        self.mt_creator = MixingTimeCreator()
    
    def setup_mixing_time_measurement(self, name: str):
        self.name = name
        self.mt_creator.create_file_structures(name)
    
    def take_empty_calibration(self):
        
        self.camera.add_task(self.camera.States.MT_EMPTY_CALIBRATION_STATE, 0)        
    
    def take_filled_calibration(self):
        
        self.camera.add_task(self.camera.States.MT_FILLED_CALIBRATION_STATE, 0)
        
    def start_mixing_time(self, handle: str, airflow: float, injection_volume: int):
        
        self.runner = MixingTimeRunner(handle, airflow, injection_volume)
        self.runner.start()
        
    def stop_mixing_time(self):
        
        self.runner.stop_event.set()
