import threading
import time
from queue import Queue

from concurrent.futures import ThreadPoolExecutor

from operator_mod.logger.global_logger import Logger

class Manager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Manager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        
        self.current_state = None
        
        # Utils
        self.logger = Logger("Algorithm Manager").logger
        
        # Trying ThreadPoolExecutor
        self.executor = ThreadPoolExecutor(max_workers=5)
    
        self.task_queue = Queue()
            
        # Necessary events        
        self.shutdown_flag = threading.Event()

        self.queue_thread = threading.Thread(target=self._process_tasks)
        self.queue_thread.daemon = True
        self.queue_thread.start()

    def __del__(self):
        self.shutdown()
        
    def shutdown(self):
        
        try:
            # First we go back to idle
            self.stop()
                        
            # Clear the task queue and task set
            while self.task_queue.qsize() > 0:
                self.task_queue.get()

            self.shutdown_flag.set()
     
            # Stop the task processing thread
            if self.queue_thread.is_alive():
                self.queue_thread.join()  # Wait for queue_thread to stop

            # Shutdown the executor for current state processing
            if self.executor:
                self.executor.shutdown()

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

        finally:
            self.logger.info("Gracefully shutdown.")

    ### Here is the state machine logic ###
    def _process_tasks(self):
        
        while not self.shutdown_flag.is_set():
            
            if not self.task_queue.empty():
                
                task = self.task_queue.get(timeout=0.25)
                mode, runtime = task
                
                state_class = self.state_classes.get(mode, None)
                
                if not state_class:
                    self.logger.error("Tried executing an unknown state.")
                    continue
            
                self.current_state = state_class(self, runtime)
                self.executor.submit(self.current_state.run)
                
                time.sleep(0.05)
            else:
                time.sleep(0.05)

    def add_task(self, mode: int, runtime: int):
        
        self.task_queue.put((mode, runtime))

    def stop(self):
        
        with self._lock:
            
            if self.current_state:
                self.current_state.terminate()
                self.executor.shutdown(wait=False)

            # Clearing the queue
            while not self.task_queue.empty():
                self.task_queue.get()

            # Fresh executor
            self.executor = ThreadPoolExecutor(max_workers=5)
    
    @classmethod
    def get_instance(cls):
        return cls._instance
    
    @property
    def get_current_state(self):
        with self._lock:
            return type(self.current_state)