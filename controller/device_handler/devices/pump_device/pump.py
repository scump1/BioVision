
import sys
sys.path.append("C:\\Users\\L. Pastwa\\AppData\\Local\\Programs\\CETONI_SDK\\lib\\python")

from qmixsdk import qmixbus # type: ignore
from qmixsdk import qmixpump # type: ignore

import time
import threading
from enum import Enum

from model.data.configuration_manager import ConfigurationManager

from operator_mod.logger.global_logger import Logger
from operator_mod.eventbus.event_handler import EventManager
from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from controller.device_handler.devices.state_machine_template import Device

from controller.device_handler.devices.pump_device.states.all_states import HealthCheckState, LoadFluidState, UnloadFluidState, MTUnloadFluidState, SyringeSetter, CalibrationState

class Pump(Device):
    
    class States(Enum):
        HEALTH_CHECK_STATE = 1
        LOAD_FLUID = 2
        UNLOAD_FLUID = 3
        MT_INJECTION_UNLOAD = 4
        SYRINGE_SETTER = 5
        CALIBRATE = 6
    
    state_classes = {
        States.HEALTH_CHECK_STATE: HealthCheckState,
        States.LOAD_FLUID: LoadFluidState,
        States.UNLOAD_FLUID: UnloadFluidState,
        States.MT_INJECTION_UNLOAD: MTUnloadFluidState,
        States.SYRINGE_SETTER: SyringeSetter,
        States.CALIBRATE: CalibrationState
        # Add more states here
    }
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Pump, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        
        super().__init__()
        
        self.logger = Logger("Pump").logger
        
        self.events = EventManager()
        self.events.add_listener(self.events.EventKeys.CONFIGURATION_SETTER_PUMP, self._syringeconfig, 0)
        
        self.config_manager = ConfigurationManager.get_instance()
        self.data = InMemoryData()
        
        self.pump = None
        self._syringe_params = None # Gets set in the connector
        self._fill_level = None
        
        self.pump_stopped_flag = False

        self.await_mt_injection_event = threading.Event()

        try:
            self._connect()
            self._start_pump()
            
            self._fill_level = self.pump.get_fill_level() # retrieveing after Bus init
        except Exception as e:
            self.logger.error(f"Could not connect to pump: {e}.")
            self.data.add_data(self.data.Keys.PUMP, False, self.data.Namespaces.DEVICES)
        
    def _connect(self):
        """
        Executes the connecting routine and sets units and syringe parameters.
        """
        ### DO NOT CHANGE
        CONST_PATH = "C:\\Users\\Public\\Documents\\QmixElements\\Projects\\default_project\\Configurations\\LP_SinglePumpConfig"
        ### DO NOT CHANGE
        
        self.logger.info(f"Opening bus with deviceconfig {CONST_PATH}.")
        self.bus = qmixbus.Bus()
        self.bus.open(CONST_PATH, "")
        
        self.logger.info("Looking up devices...")
        self.pump = qmixpump.Pump()
        self.pump.lookup_by_name("neMESYS_Starter_1_Pump")
                
        self._set_units()
        self._syringeconfig()
                
        self.max_volume = self.pump.get_volume_max()
        self.max_flowrate = self.pump.get_flow_rate_max()
            
    def _start_pump(self):
        
        self.logger.info("Starting bus communication.")
        self.bus.start()
        
        self.logger.info("Enabling pump drive.")
        if self.pump.is_in_fault_state():
            self.pump.clear_fault()
            
        if not self.pump.is_enabled():
            self.pump.enable(True)     
    
    def __del__(self):
        
        super().__del__()
        
        if self.pump.is_enabled():
            self.pump.enable(False)
        
        if self.bus:
            self.bus.stop()
            self.bus.close()
    
    ### Functionality
    
    def load_fluid(self, volume: int):
        """
        Loads an amount of fluid 'volume' with maximum flow rate.
        """
        
        if volume >= self.max_volume:
            volume = self.max_volume
        
        if volume >= (self.max_volume - float(self._fill_level)):
            volume = (self.max_volume - float(self._fill_level))
        
        self.pump.aspirate(volume, self.max_flowrate)
        self._wait_load_fluid(volume, self.max_flowrate)
    
    def unload_fluid(self, volume:int , flowrate: int):
        """
        'Unloads' (dispenses) an amount of fluid via the syringe.
        """
        if flowrate >= self.max_flowrate:
            flowrate = self.max_flowrate
        
        if volume >= self.pump.get_fill_level():
            volume = self.pump.get_fill_level()
            
        self.pump.dispense(float(volume), float(flowrate))    
        self._wait_dipsense_fluid(volume, flowrate)
    
    def start_calibration(self) -> None:
        
        try:
            self.pump.calibrate()
            self._wait_calibration_finished()
        except Exception as e:
            self.logger.error(f"Exception during calibration routine: {e}.")
    
    def stop_pump(self):
        
        try:
            self.pump_stopped_flag = True
            self.pump.stop_pumping()
        
        except Exception as e:
            self.logger.error(f"Could not stop pump: {e}.")
    
    ### Internal setup via SDK    
    def _set_units(self):
        """
        Sets the pump units to microliters for better handling.
        """
        self.pump.set_volume_unit(qmixpump.UnitPrefix.micro, qmixpump.VolumeUnit.litres)
        max_ul = self.pump.get_volume_max()
        self.logger.info(f"Max. volume uL: {max_ul}.")

        self.pump.set_flow_unit(qmixpump.UnitPrefix.micro, qmixpump.VolumeUnit.litres, qmixpump.TimeUnit.per_second)
        max_ul_s = self.pump.get_flow_rate_max()
        self.logger.info(f"Max. flow ul/s: {max_ul_s}.")
    
    def _syringeconfig(self, diameter : float = None, length : float = None):
        """
        Sets the syringe parameters to the pump device or loads a configuration if none are given.
        
        Args:
            diameter (float): A new syringe diameter in mm
            length (float): A new sringe diameter in mm (typically 50 or 60)
        """
        try:
            if diameter is None and length is None:

                setting = self.config_manager.get_configuration(self.config_manager.Devices.PUMP)
                
                init_diameter = setting[self.config_manager.PumpSettings.SYRINGE_DIAMETER] if self.config_manager.PumpSettings.SYRINGE_DIAMETER in setting else 7.97
                init_length = setting[self.config_manager.PumpSettings.SYRINGE_LENGTH]if self.config_manager.PumpSettings.SYRINGE_LENGTH in setting else 50.0
                
                if init_diameter is not None and init_length is not None:
                    self.pump.set_syringe_param(float(init_diameter), float(init_length))
            else:
                self.pump.set_syringe_param(diameter, length)
                
            diameter, stroke = self.pump.get_syringe_param()
            
            self._syringe_params = [diameter, stroke]
            
            self.max_volume = self.pump.get_volume_max()
            self.max_flowrate = self.pump.get_flow_rate_max()
            
            self.logger.info("Setup of syringe successful.")
        except Exception as e:
            self.logger.warning(f"Error in syringe config setting: {e}.")
  
    ### Internal waiting and checkups
    def _wait_calibration_finished(self, timeout : int = 30):
        """
        The function waits until the given pump has finished calibration or
        until the timeout occurs.
        """
        timer = 0
        result = False
        while (result == False) and (timer <= timeout) and not self.pump_stopped_flag:
            result = self.pump.is_calibration_finished()
            self._fill_level = self.pump.get_fill_level()
            timer += 0.5
            time.sleep(0.5)
        
        self.pump_stopped_flag = False
        
        return result

    def _wait_load_fluid(self, volume: float, flow: float):
        """
        Waits the given timeframe for aspiration/dispension
        """
        if volume and flow:
            target_fill = self.pump.get_fill_level() + volume
            timeframe = volume/flow + 1 # one extra seconds for things to finish
            timer = 0
            result = False
            
            while (result == False) and timer <= timeframe and not self.pump_stopped_flag:
                self._fill_level = self.pump.get_fill_level()
                if abs(self._fill_level - target_fill) <= 5:
                    result = True

                timer += 0.5
                time.sleep(0.5)
            
            self.pump_stopped_flag = False

            return result
            
        else:
            self.logger.warning(f"Tried waiting for dipsensing {volume} uL with {flow} uL/s.")
            return 

    def _wait_dipsense_fluid(self, volume: float, flow: float):
        """
        Waits the given timeframe for aspiration/dispension
        """
        if volume and flow:
            target_fill = max(0, self.pump.get_fill_level() - volume)
            timeframe = volume/flow + 1 # one extra seconds for things to finish
            timer = 0
            result = False
            
            while (result == False) and timer <= timeframe and not self.pump_stopped_flag:
                self._fill_level = self.pump.get_fill_level()
                if abs(self._fill_level - target_fill) <= 5:
                    result = True
                
                timer += 0.5
                time.sleep(0.5)
            
            self.pump_stopped_flag = False
            
            return result

        else:
            self.logger.warning(f"Tried waiting for dipsensing {volume} uL with {flow} uL/s.")
            return 

    @property
    def fill_level(self):
        return self._fill_level

    @property
    def syringe_params(self):
        return self._syringe_params

    @classmethod
    def get_instance(cls):
        return cls._instance