

from controller.device_handler.devices.camera_device.camera import Camera
from model.measurements.mixing_time_creator import MixingTimeCreator

class MixingTimeHandler:
    
    def __init__(self):
        
        self.camera = Camera.get_instance()
        
        self.mt_creator = MixingTimeCreator()
    
    def setup_mixing_time_measurement(self, name: str):

        self.mt_creator.create_file_structures(name)
    
    def take_empty_calibration(self):
        
        self.camera.add_task(self.camera.States.MT_EMPTY_CALIBRATION_STATE, 0)        
    
    def take_filled_calibration(self):
        
        self.camera.add_task(self.camera.States.MT_FILLED_CALIBRATION_STATE, 0)