
import threading
import time

from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from operator_mod.logger.global_logger import Logger
from operator_mod.logger.progress_logger import ProgressLogger

from controller.device_handler.devices.camera_device.camera import Camera
from controller.device_handler.devices.pump_device.pump import Pump
from controller.device_handler.devices.mfc_device.mfc import MFC

class MixingTimeRunner(threading.Thread):
    """A class for running mixing time measurements."""
    
    _instance = None
    runtime : int = 15
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MixingTimeRunner, cls).__new__(cls)
        return cls._instance
        
    def __init__(self, handle : str, airflow: int, injection_volume: int):
        
        threading.Thread.__init__(self)
        self.daemon = True
        
        self.airflow = airflow
        self.injection_volume = injection_volume
        
        self.camera  = Camera.get_instance()
        self.pump = Pump.get_instance()
        self.mfc = MFC.get_instance()
        
        self.data = InMemoryData()
        self.logger = Logger("Application").logger
        
        self.stop_event = threading.Event()
        
        self.progess_logger = ProgressLogger(handle)
        
    def run(self):
        
        self.prepare()
        timer = 0
 
        ### here the MFC already has the massflow set, so now we start the image cap and after 2.5 seconds the injection
        self.camera.mt_await_capture_start_event.set()
        
        while not self.stop_event.is_set() and timer <= 2:
            timer += 0.1
            time.sleep(0.1)
        
        self.progess_logger.progress_space('mixing_time', 2)
        self.pump.await_mt_injection_event.set()
        
        while not self.stop_event.is_set() and timer <= self.runtime:
            self.logger.info("Mixing time runner in progress.")
            timer += 1
            self.progess_logger.progress_space('mixing_time', 1)
            time.sleep(1)
        
        self.cleanup()
        
    def prepare(self):
        """
        Brings the camera, mfc and pump into the correct state for the measurement. Alles devices have a threading.Event() to wait for their start.
        """
        # Camera
        self.camera.add_task(self.camera.States.MT_IMAGE_CAPTURE_STATE, self.runtime)
        
        # Pump
        self.data.add_data(self.data.Keys.PUMP_UNLOAD_VOLUME, self.injection_volume, namespace=self.data.Namespaces.PUMP)
        self.pump.add_task(self.pump.States.MT_INJECTION_UNLOAD, 0)
        
        # MFC
        self.data.add_data(self.data.Keys.MFC_SETTINGS, self.airflow, namespace=self.data.Namespaces.MFC)
        self.mfc.add_task(self.mfc.States.SETTING_SETTER_STATE, 0)
        
        time.sleep(1)
        # Check for success
        success : bool = self.data.get_data(self.data.Keys.MFC_SETTINGS_SUCCESS, self.data.Namespaces.MFC)
        if not success:
            self.stop_event.set()
            
        # The progress logger
        self.progess_logger.add_scorespace('mixing_time', self.runtime)
        
    def cleanup(self):
        
        self.progess_logger.del_scorespace('mixing_time', True)

        self.camera.stop()
        self.pump.stop()
        self.mfc.stop()