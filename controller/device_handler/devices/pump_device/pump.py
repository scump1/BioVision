
import sys
sys.path.append("C:\\Users\\L. Pastwa\\AppData\\Local\\Programs\\CETONI_SDK\\lib\\python")

from qmixsdk import qmixbus # type: ignore
from qmixsdk import qmixpump # type: ignore

import time
import threading
from enum import Enum

from operator_mod.logger.global_logger import Logger
from operator_mod.eventbus.event_handler import EventManager
from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from controller.device_handler.devices.state_machine_template import Device

from controller.device_handler.devices.pump_device.states.all_states import HealthCheckState, LoadFluidState, UnloadFluidState, MTUnloadFluidState

class Pump(Device):
    
    class States(Enum):
        HEALTH_CHECK_STATE = 1
        LOAD_FLUID = 2
        UNLOAD_FLUID = 3
        MT_INJECTION_UNLOAD = 4
    
    state_classes = {
        States.HEALTH_CHECK_STATE: HealthCheckState,
        States.LOAD_FLUID: LoadFluidState,
        States.UNLOAD_FLUID: UnloadFluidState,
        States.MT_INJECTION_UNLOAD: MTUnloadFluidState
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
        self.data = InMemoryData()
        
        self.pump = None
        self._syringe_params = None # Gets set in the connector

        self.await_mt_injection_event = threading.Event()

        self._connect()
        self._start_pump()
        
        self._fill_level = self.pump.get_fill_level() # retrieveing after Bus init
        
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
            
        self.logger.info("Calibrating pump.")
        self.pump.calibrate()

        calibration_finished = self._wait_calibration_finished()
        if calibration_finished:
            self.logger.info(f"Pump calibrated: {calibration_finished}.")
            
        else:
            self.logger.error(f"Could not calibrate pump: {calibration_finished}.")        
    
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
        
        elif volume >= (self.max_volume - float(self._fill_level)):
            volume = (self.max_volume - float(self._fill_level))
        
        self.pump.aspirate(volume, self.max_flowrate)
        self._wait_load_fluid(volume, self.max_flowrate)
    
    def unload_fluid(self, volume:int , flowrate: int):
        """
        'Unloads' (dispenses) an amount of fluid via the syringe.
        """
        if flowrate >= self.max_flowrate:
            flowrate = self.max_flowrate
        
        elif volume >= self.pump.get_fill_level():
            volume = self.pump.get_fill_level()
            
        self.pump.dispense(float(volume), float(flowrate))    
        self._wait_dipsense_fluid(volume, flowrate)
    
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
    
    def _syringeconfig(self):
        """
        Sets the intended syringe configuration to the pump.
        """
        inner_diameter_set = 8.0
        piston_stroke_set = 50.0
        self.pump.set_syringe_param(inner_diameter_set, piston_stroke_set)
        diameter, stroke = self.pump.get_syringe_param()
        
        if diameter == inner_diameter_set and stroke == piston_stroke_set:
            self._syringe_params = [diameter, stroke]
            self.logger.info("Setup of syringe successful.")
        else:
            return
  
    ### Internal waiting and checkups
    def _wait_calibration_finished(self, timeout : int = 30):
        """
        The function waits until the given pump has finished calibration or
        until the timeout occurs.
        """
        timer = 0
        result = False
        while (result == False) and (timer <= timeout):
            result = self.pump.is_calibration_finished()
            timer += 0.5
            time.sleep(0.5)
            
        return result

    def _wait_load_fluid(self, volume: float, flow: float):
        """
        Waits the given timeframe for aspiration/dispension
        """
        if volume and flow:
            target_fill = self.pump.get_fill_level() + volume
            timeframe = volume/flow + 2 # two extra seconds for things to finish
            timer = 0
            result = False
            
            while (result == False) and timer <= timeframe:
                self._fill_level = self.pump.get_fill_level()
                if abs(self._fill_level - target_fill) <= 5:
                    result = True

                timer += 0.5
                time.sleep(0.5)
                
            return result
            
        else:
            self.logger.warning(f"Tried waiting for dipsensing {volume} uL with {flow} uL/s.")
            return 

    def _wait_dipsense_fluid(self, volume: float, flow: float):
        """
        Waits the given timeframe for aspiration/dispension
        """
        if volume and flow:
            target_fill = self.pump.get_fill_level() - volume
            timeframe = volume/flow + 2 # two extra seconds for things to finish
            timer = 0
            result = False
            
            while (result == False) and timer <= timeframe:
                self._fill_level = self.pump.get_fill_level()
                if abs(self._fill_level - target_fill) <= 5:
                    result = True
                
                timer += 0.5
                time.sleep(0.5)
                
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