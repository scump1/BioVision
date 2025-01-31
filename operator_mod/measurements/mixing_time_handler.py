

from model.measurements.mixing_time_creator import MixingTimeCreator

class MixingTimeHandler:
    
    def __init__(self):
        
        self.mt_creator = MixingTimeCreator()
    
    def setup_mixing_time_measurement(self, name: str):

        self.mt_creator.create_file_structures(name)
    
    def start_mixing_time_measurement(self):
        pass
    
    def stop_mixing_time_measurement(self):
        pass