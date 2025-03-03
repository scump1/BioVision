
import queue
import threading
import time
import serial

from enum import Enum
from controller.device_handler.devices.arduino_device.states.all_states import HealthCheckState, SettingsSetterState, SensorPolling, LightSwitch

from operator_mod.logger.global_logger import Logger
from operator_mod.eventbus.event_handler import EventManager
from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from controller.device_handler.devices.state_machine_template import Device

class Arduino(Device):
    
    _instance = None
    _lock = threading.Lock()
    
    class States(Enum):
        HEALTH_CHECK_STATE = 1
        SETTING_SETTER_STATE = 2
        SENSOR_POLLING_STATE = 3
        LIGHT_SWITCH_STATE = 4
    
    state_classes = {
        States.HEALTH_CHECK_STATE: HealthCheckState,        
        States.SETTING_SETTER_STATE: SettingsSetterState,
        States.SENSOR_POLLING_STATE: SensorPolling,
        States.LIGHT_SWITCH_STATE: LightSwitch
        # Add more states here
    }

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Arduino, cls).__new__(cls)
        return cls._instance

    def __init__(self):
            
        super().__init__()
        
        # Threading Events
        self.await_polling_start_event = threading.Event()
        
        # Serial Management
        self.serial_command_queue = queue.Queue()
        self.serial_lock = threading.Lock()
        self.serial_worker_thread = threading.Thread(target=self._serial_worker)
        self.serial_worker_thread.daemon = True
        self.serial_worker_thread.start()
        
        self.logger = Logger("Arduino").logger
        self.events = EventManager()
        self.data = InMemoryData()
        
        # Modifying the amount of arduino states here -> for lightswitching
        self.executor._max_workers = 2
        
        self.serial_con = None
        self._connect()
            
    ### Arduino Handling ###
    def _connect(self):

        try:
            if self.serial_con is None:
                self.serial_con = serial.Serial("COM6", 115200, timeout=3)
                time.sleep(3)
                
            if self.serial_con is not None:
                if not self.serial_con.is_open:
                    self.serial_con.open()
                self.data.add_data(self.data.Keys.ARDUINO, True, namespace=self.data.Namespaces.DEVICES)
            else:
                self.logger.error("Error in establishing serial connection: No serial connection.")
                
        except Exception as e:
            self.serial_con = None
            self.data.add_data(self.data.Keys.ARDUINO, False, namespace=self.data.Namespaces.DEVICES)
            self.logger.warning(f"Error in establishing serial connection: {e}")

    def _serial_worker(self):
        """Runs the serial communication and collects multi-line responses when necessary."""
        while True:
            command, response_event, response_list = self.serial_command_queue.get()

            with self.serial_lock:
                
                if self.serial_con.writable():
                    try:
                        # Send command
                        self.serial_con.write(f"{command}\n".encode())
                        self.logger.info(f"Sent command: {command}")

                        # Handle multi-line response
                        if command == "R":
                            expected_lines = 3  # "R" command returns 3 lines
                        else:
                            expected_lines = 1  # Other commands return only 1 line

                        for _ in range(expected_lines):
                            response = self.serial_con.readline().decode().strip()
                            if response:
                                response_list.append(response)
                                self.logger.info(f"Received response: {response}")

                    except serial.SerialException as e:
                        self.logger.error(f"Serial error: {e}")
                    except Exception as e:
                        self.logger.error(f"Unexpected error: {e}")

            # Signal that the response is ready
            response_event.set()

    def send_command(self, command):
        """
        Places a command in the queue and waits for the full response.
        Returns a list of responses if multiple lines are expected.
        """
        response_event = threading.Event()
        response_list = []
        
        self.serial_command_queue.put((command, response_event, response_list))
        response_event.wait()  # Wait until response is ready

        return response_list if response_list else None


    @classmethod
    def get_instance(cls):
        return cls._instance