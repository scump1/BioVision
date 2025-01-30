
from apscheduler.schedulers.background import BackgroundScheduler

from operator_mod.logger.global_logger import Logger
from controller.device_handler.device_handler_class.device_handler import DeviceHandler
from controller.algorithms.algorithm_manager_class.algorithm_manager import AlgorithmManager

class Controller:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Controller, cls).__new__(cls)
        return cls._instance

    def __init__(self):

        self.logger = Logger("Controller").logger
        self.health_check_scheduler = BackgroundScheduler()

    def start_controller(self):

        # This is an runtime thread that exists throughout the application runtime. Thats why its a deamon thread that kills itslef when application ends.
        self.device_handler = DeviceHandler()
        self.alg_man = AlgorithmManager()
        
        self.health_check_scheduler.add_job(self.health_checker, 'interval', seconds=10)
        self.health_check_scheduler.start()
        
    def health_checker(self):
        self.device_handler.add_task(self.device_handler.States.HEALTH_CHECK_STATE, 0)
                
    def shutdown(self):
        
        try:
            self.health_check_scheduler.shutdown(wait=False)
            
            self.device_handler.shutdown()
            self.alg_man.shutdown()
                        
        except Exception as e:
            self.logger.error(f"Shutdown error: {e}")
