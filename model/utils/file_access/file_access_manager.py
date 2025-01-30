import threading
import queue

from operator_mod.logger.global_logger import Logger

class FileAccessManager:
    
    def __init__(self):
        self.locks = {}
        self.queues = {}
        self.global_lock = threading.Lock()
        self.logger = Logger("FileAccessManager").logger
        self.logger.info("FileAccessManager initialized.")

    def get_access(self, path):
        self.logger.info(f"Requesting access for {path} by {threading.current_thread().name}")
        with self.global_lock:
            if path not in self.locks:
                self.locks[path] = threading.Lock()
                self.queues[path] = queue.Queue()
                self.logger.info(f"Created new lock and queue for {path}")

        file_lock = self.locks[path]
        file_queue = self.queues[path]
        
        file_queue.put(threading.current_thread())
        self.logger.info(f"{threading.current_thread().name} added to queue for {path}")

        while file_queue.queue[0] is not threading.current_thread():
            pass
        
        file_lock.acquire()
        self.logger.info(f"{threading.current_thread().name} acquired lock for {path}")

    def release_access(self, path):
        self.logger.info(f"Releasing access for {path} by {threading.current_thread().name}")
        with self.global_lock:
            if path in self.locks:
                file_lock = self.locks[path]
                file_queue = self.queues[path]
                
                if file_lock.locked():
                    file_lock.release()
                    self.logger.info(f"{threading.current_thread().name} released lock for {path}")
                    file_queue.get()
                    self.logger.info(f"{threading.current_thread().name} removed from queue for {path}")

    def __del__(self):
        self.logger.info("FileAccessManager is being destroyed. Releasing all locks.")
        # Ensure all locks are released when the manager is destroyed
        for path, lock in self.locks.items():
            if lock.locked():
                lock.release()
                print(f"Released lock for {path}")