
import copy
import datetime
import threading
import time

from controller.algorithms.algorithm_manager_class.algorithm_manager import AlgorithmManager
from controller.device_handler.devices.arduino_device.arduino import Arduino
from controller.device_handler.devices.camera_device.camera import Camera
from controller.device_handler.devices.mfc_device.mfc import MFC

from model.measurements.routine_system.routine_system import RoutineData, RoutineSystem

from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from operator_mod.logger.global_logger import Logger
from operator_mod.logger.progress_logger import ProgressLogger
from operator_mod.eventbus.event_handler import EventManager

from model.utils.resource_manager import ResourceManager

class MeasurementRunner(threading.Thread):
    
    """Handles the correct execution of a routine configured from the measurement setter.
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MeasurementRunner, cls).__new__(cls)
        return cls._instance
        
    def __init__(self, routine: RoutineSystem):
        
        threading.Thread.__init__(self)
        self.daemon = True
        
        # The devices
        self.arduino = Arduino.get_instance()
        self.camera = Camera.get_instance()
        self.mfc = MFC.get_instance()
        
        # Processing
        self.algman = AlgorithmManager.get_instance()
        
        # Utils
        self.logger = Logger("Application").logger
        self.data = InMemoryData()
        self.events = EventManager.get_instance()

        self.resman = ResourceManager.get_instance()       
        
        # Data
        self.routine = routine
        self.slots = copy.deepcopy(self.routine.slots) # Else we would modify the routine directly which would cause errors when trying to restart
        
        self.progress_logger = ProgressLogger(routine.name) # Create one progresslogger for the routine where we add every slot individually

        # End Flag
        self.stop_flag = threading.Event()
        
        # Flag for slot_condition
        self.slot_condition_reached = False
    
        # Flags for toggling stuff
        self.alg_flag = False
        self.arduino_flag = False
        self.cam_flag = False
        self.stopwait_flag = False
        self.condition_flag = False
    
    def __del__(self):
        self.shutdown()
    
    def shutdown(self):
        
        self.logger.info("Deleted Measurement Runner instance.")
    
    ### Run
    def run(self):
       
        while not self.stop_flag.is_set():

            # Process the slot scenario
            self.setup_slot_scenario()
            
            if self.stop_flag.is_set():
                                    
                self.reset_flags_and_devices()
                self.logger.info("Terminating current Measurement.")
                break
            
            # Here we start the actual measurement - This synchronization schedule is enough to be accurate                
            if self.arduino_flag:
                self.arduino.add_task(self.arduino.States.SENSOR_POLLING_STATE, self.runtime_seconds)
                self.arduino.await_polling_start_event.set()
       
            if self.cam_flag:
                self.camera.add_task(self.camera.States.IMAGE_CAPTURE_STATE, self.runtime_seconds)
                self.camera.await_capture_start_event.set()
         
            if self.alg_flag:
                # What algorithm and whatnot is done in the slot setup
                self.algman.measurement_start_event.set()
            
            self.events.trigger_event(self.events.EventKeys.MS_PROGRESS_SLOT, self.routine.name, self.slotname)
            
            # This is for each slot
            while datetime.datetime.now() < self.runtime and not self.slot_condition_reached:
                
                if self.stop_flag.is_set():
                    break
                
                if self.condition_flag:
                    self._condition_checker(None, False) #This checks the current set condition to be true or not
                
                diff = self.runtime_seconds - (self.runtime - datetime.datetime.now()).total_seconds() + 1
                diff = round(diff)
                
                if type(diff) is int and diff >= 0:
                    self.progress_logger.set_space_value(self.slotname, diff)

                time.sleep(1)
            
            if self.slot_condition_reached:
                self.logger.info("Reached Slot condition. Continuing.")
                self.slot_condition_reached = False # Resetting this flag for the next slot immediately
            
            if self.stop_flag.is_set():
                                    
                self.reset_flags_and_devices()
                self.logger.info("Terminating current Measurement.")
                break
            
            if self.stopwait_flag:
                
                self.events.trigger_event(self.events.EventKeys.MS_STOPPED_FOR_WAITING)
                
                time.sleep(1)
                while not self.data.get_data(self.data.Keys.MEASUREMENT_STOPPED_AND_WAITING, self.data.Namespaces.MEASUREMENT) and not self.stop_flag.is_set():
                    time.sleep(1)
                
            # Reset to normal
            self.reset_flags_and_devices()
            
            _, target, _ = self.progress_logger.get_progress(self.slotname)
            self.progress_logger.set_space_value(self.slotname, target)
            
            self.logger.info("Switiching to next slot.")

        self.reset_flags_and_devices()

        # Purgin the Scorespace
        self.progress_logger.del_scorespace(self.slotname, True)
    
        self.logger.info("Finished the Measurement sucessfully.")
        self.events.trigger_event(self.events.EventKeys.MS_ENDED)
        
                
    def reset_flags_and_devices(self):
        
        self.alg_flag = False
        self.arduino_flag = False
        self.cam_flag = False    
    
        self.arduino.await_polling_start_event.clear()
        self.camera.await_capture_start_event.clear()
        self.algman.measurement_start_event.clear()
        
        self.data.add_data(self.data.Keys.CAMERA_LIGHTSWITCHING, False, self.data.Namespaces.MEASUREMENT)
        
        self.device_resetter()
    
    def device_resetter(self):
        
        self.camera.stop()
        self.arduino.stop()
        self.mfc.stop()
        self.algman.stop()

    def setup_slot_scenario(self) -> None:
        
        if not len(self.slots) > 0:
            self.logger.info("All Slots done.")
            self.stop_flag.set()
            return
        
        slot = self.slots.pop(0)

        self.slotname = slot.name
        self.runtime_seconds = slot.runtime
        
        # creating the progress log for each slot new!
        self.progress_logger.add_scorespace(slot.name, slot.runtime)
        
        # Here we set the appropiate paths in the memory store
        paths = self.resman.get_registered_resources(self.slotname, True, True)
        
        if paths:
            self.data.add_data(self.data.Keys.CURRENT_SLOT_FOLDER, paths[self.slotname], self.data.Namespaces.MEASUREMENT)
            self.data.add_data(self.data.Keys.CURRENT_SLOT_FOLDER_CALIBRATION, paths["Calibration"], self.data.Namespaces.MEASUREMENT)
            self.data.add_data(self.data.Keys.CURRENT_SLOT_FOLDER_RESULT, paths["Result"], self.data.Namespaces.MEASUREMENT)
            self.data.add_data(self.data.Keys.CURRENT_SLOT_FOLDER_IMAGES, paths["Images"], self.data.Namespaces.MEASUREMENT)
            self.data.add_data(self.data.Keys.CURRENT_SLOT_RESULT_DB, paths["DB"], self.data.Namespaces.MEASUREMENT)
        else:
            self.logger.error("Couldn't fetch all paths from Ressource Manager.")
            self.stop_flag = True
            return
        
        # Proceeding with setting up the slot
        self.stopwait_flag = True if slot.interaction is not None else False

        # Setup of the resourcespace - this gets automatically fetched by camera and algman when needed
        self.data.add_data(self.data.Keys.CURRENT_RESOURCE_SPACE, slot.uid, self.data.Namespaces.MEASUREMENT)
        
        camset = []
        
        if slot.condition is not None:
            self.condition_flag = True
            self._condition_checker(slot.condition, True)
        
        if slot.settings:
            for setting in slot.settings:
                            
                if setting.name == RoutineData.Parameter.TEMPERATURE:
                    
                    self.arduino_flag = True
                    temperature = setting.setting.target
                    
                    if self.condition_flag:
                        if slot.condition.parameter == RoutineData.Parameter.TEMPERATURE:
                            self.arduino_settings_setter(temperature, True)
                    else:
                        self.arduino_settings_setter(temperature)
            
                elif setting.name == RoutineData.Parameter.ALGORITHMS:
                    
                    algorithm = setting.setting.algorithm
                    self.algorithm_man_setter(algorithm)
                    
                elif setting.name == RoutineData.Parameter.CAMERA:

                    self.cam_flag = True
                    camset.append(setting.setting.img_count) 
                    camset.append(setting.setting.interval) 

                    self.camera_settings_setter(camset)
                    
                elif setting.name == RoutineData.Parameter.MFC:
                    
                    massflow = setting.setting.massflow
                    interrupt = setting.setting.interrupt
                    self.mfc_settings_setter(massflow, interrupt)       
                    
                elif setting.name == RoutineData.Parameter.LIGHTMODE:
                    
                    lightmode = setting.setting.mode
                    self.lightmode_setter(lightmode)
                
        else:
            self.logger.warning(f"No setting in current slot {slot}.")
            
        # At last we take the runtime
        self.runtime = datetime.datetime.now() + datetime.timedelta(seconds=slot.runtime + 1) # This extra second is important dont ask why :=)
    
    def _condition_checker(self, slot_condition, setter=False):
        
        if setter is True:
            condition = slot_condition
        
        if setter is False:
            
            if condition.parameter == RoutineData.Parameter.TEMPERATURE:
                data = self.data.get_data(self.data.Keys.LIVE_TEMPERATURE, namespace=self.data.Namespaces.MEASUREMENT)
    
                result = condition.evaluate(data)
                
                if result is True:
                    self.slot_condition_reached = True

    def arduino_settings_setter(self, temperature, live_record = False):
        
        self.data.add_data(self.data.Keys.TEMPERATURE_SETTING, temperature, namespace=self.data.Namespaces.ARDUINO)
        self.data.add_data(self.data.Keys.LIVE_RECORDING, live_record, namespace=self.data.Namespaces.ARDUINO)
        
        self.arduino.add_task(self.arduino.States.SETTING_SETTER_STATE, 0)
        
    def camera_settings_setter(self, settings: list):

        # The ImageCapture
        self.data.add_data(self.data.Keys.CAMERA_SETTINGS, settings, namespace=self.data.Namespaces.CAMERA)
        
    def mfc_settings_setter(self, massflow: float, interrupt: bool):
        
        self.data.add_data(self.data.Keys.CAMERA_MASSFLOW_INTERRUPT, interrupt, self.data.Namespaces.MEASUREMENT) # this sets a flag for the camera 
        self.data.add_data(self.data.Keys.MFC_SETTINGS, massflow, namespace=self.data.Namespaces.MFC)
        self.mfc.add_task(self.mfc.States.SETTING_SETTER_STATE, 0)    
    
    def algorithm_man_setter(self, algorithm):
        
        # TBD implementing multiple things
        self.alg_flag = True
        
        # Checking the different algorithms
        if algorithm == RoutineData.AlgorithmType.BUBBLE_SIZE:
            self.algman.add_task(self.algman.States.BUBBLE_SIZER_STATE, self.runtime_seconds)
            
        elif algorithm == RoutineData.AlgorithmType.PELLET_SIZE:
            # TBD
            pass
    
    def lightmode_setter(self, lightmode):
        
        # If it should be off we just switch it off via the arduino
        if lightmode == RoutineData.LightMode.ALWAYS_OFF:
            
            self.data.add_data(self.data.Keys.LIGHTMODE, False, self.data.Namespaces.MEASUREMENT)
            self.arduino.add_task(self.arduino.States.LIGHT_SWITCH_STATE, 0)
        
        # Only one when needed means the camera sends a signal to the arudino before taking a pic
        elif lightmode == RoutineData.LightMode.ON_WHEN_NEEDED:
            
            self.data.add_data(self.data.Keys.CAMERA_LIGHTSWITCHING, True, self.data.Namespaces.MEASUREMENT)
            # This will be checked during the camera imagecapture state and schedules the event for the arduino
            
        elif lightmode == RoutineData.LightMode.ALWAYS_ON:
            
            self.data.add_data(self.data.Keys.LIGHTMODE, True, self.data.Namespaces.MEASUREMENT)
            self.arduino.add_task(self.arduino.States.LIGHT_SWITCH_STATE, 0)