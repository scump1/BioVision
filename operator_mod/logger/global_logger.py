import logging
import os
from logging.handlers import RotatingFileHandler
from threading import Lock

class Logger:
    
    _instances = {}
    _lock = Lock()

    def __new__(cls, name):
        with cls._lock:
            if name not in cls._instances:
                instance = super().__new__(cls)
                instance._init_logger(name)
                cls._instances[name] = instance
        return cls._instances[name]

    def _init_logger(self, name):

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        log_file = f"{name}.log"

        # Ensuring the log directory exists
        os.makedirs('logs', exist_ok=True)
        log_path = os.path.join('logs', log_file)

        # Creating a file handler
        handler = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=2)
        handler.setLevel(logging.DEBUG)

        # Creating console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)

        # Creating a logging format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Adding the handler to the logger
        self.logger.addHandler(handler)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger
