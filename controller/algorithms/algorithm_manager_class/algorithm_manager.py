from enum import Enum
import threading

from operator_mod.logger.global_logger import Logger

from controller.algorithms.algorithm_manager_class.states.all_states import BubbleSizerState, BubbleSizerSingleState, PelletSizerSingleState, MixingTimerState
from controller.algorithms.algorithm_manager_class.abc_class.state_machine_template import Manager

class AlgorithmManager(Manager):

    _instance = None
    _lock = threading.Lock()
    
    class States(Enum):
        PELLET_SIZER_SINGLE_STATE = 0
        
        BUBBLE_SIZER_STATE = 2
        BUBBLE_SIZER_STATE_SINGLE = 3
        
        MIXING_TIMER_STATE = 5
    
    state_classes = {
        States.PELLET_SIZER_SINGLE_STATE: PelletSizerSingleState,
        States.BUBBLE_SIZER_STATE: BubbleSizerState,
        States.BUBBLE_SIZER_STATE_SINGLE: BubbleSizerSingleState,
        States.MIXING_TIMER_STATE: MixingTimerState
        # Add more states here
    }

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AlgorithmManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        
        super().__init__()
        self.logger = Logger("Algorithm Manager").logger
        
        # Synchronization
        self.measurement_start_event = threading.Event()
        self.shutdown_flag = threading.Event()
                
        # Trying ThreadPoolExecutor
        self.executor._max_workers = 5
        
        self.logger.info("Algorithm Manager initialized and ready for work.")

    @classmethod
    def get_instance(cls):
        return cls._instance