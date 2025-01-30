import sys
import time
sys.path.append("C:\\Users\\L. Pastwa\\AppData\\Local\\Programs\\CETONI_SDK\\lib\\python")

from qmixsdk import qmixbus # type: ignore
from qmixsdk import qmixpump # type: ignore

class Pump:
    
    def __init__(self):
        
        ### DO NOT CHANGE
        CONST_PATH = "C:\\Users\\Public\\Documents\\QmixElements\\Projects\\default_project\\Configurations\\LP_SinglePumpConfig"
        ### DO NOT CHANGE
        
        print("Opening bus with deviceconfig ", CONST_PATH)
        self.bus = qmixbus.Bus()
        self.bus.open(CONST_PATH, "")
        
        print("Looking up devices...")
        self.pump = qmixpump.Pump()
        self.pump.lookup_by_name("neMESYS_Starter_1_Pump")
        
        print(self.pump)
        
        self._set_units()
        self._syringeconfig()
                
        self.max_volume = self.pump.get_volume_max()
        self.max_flowrate = self.pump.get_flow_rate_max()
        
    def start_pump(self):
        
        print("Starting bus communication...")
        self.bus.start()
        
        print("Enabling pump drive...")
        if self.pump.is_in_fault_state():
            self.pump.clear_fault()
        if not self.pump.is_enabled():
            self.pump.enable(True)
            
        print("Calibrating pump...")
        self.pump.calibrate()
        time.sleep(0.2)
        calibration_finished = self.wait_calibration_finished(self.pump, 30)
        print("Pump calibrated: ", calibration_finished)
    
    def shutdown(self):
        
        pass
    
    def load_fluid(self, volume: int):
        """
        Loads an amount of fluid 'volume' with maximum flow rate.
        """
        
        if volume >= self.max_volume:
            volume = self.max_volume
        
        self.pump.aspirate(volume, self.max_flowrate)
        self.wait_dosage_finished(self.pump, 30)
    
    def unload_fluid(self, volume:int , flowrate: int):
        """
        'Unloads' (dispenses) an amount of fluid via the syringe.
        """
        if flowrate >= self.max_flowrate:
            flowrate = self.max_flowrate
        
        elif volume >= self.pump.get_fill_level():
            volume = self.pump.get_fill_level()
            
        self.pump.dispense(float(volume), float(flowrate))
        self.wait_dosage_finished(self.pump, 30)
    
    def _set_units(self):
        """
        Sets the pump units to microliters for better handling.
        """
        print("Testing SI units...")
        self.pump.set_volume_unit(qmixpump.UnitPrefix.micro, qmixpump.VolumeUnit.litres)
        max_ml = self.pump.get_volume_max()
        print("Max. volume ml: ", max_ml, self.pump.get_volume_unit())

        self.pump.set_flow_unit(qmixpump.UnitPrefix.micro, qmixpump.VolumeUnit.litres, 
            qmixpump.TimeUnit.per_second)
        max_ml_s = self.pump.get_flow_rate_max()
        print("Max. flow ml/s: ", max_ml_s, self.pump.get_flow_unit())
    
    def _syringeconfig(self):
        """
        Sets the intended syringe configuration to the pump.
        """
        inner_diameter_set = 8.0
        piston_stroke_set = 50.0
        self.pump.set_syringe_param(inner_diameter_set, piston_stroke_set)
        diameter, stroke = self.pump.get_syringe_param()
        
        if diameter == inner_diameter_set and stroke == piston_stroke_set:
            pass
        else:
            return
    
    @staticmethod
    def wait_calibration_finished(pump, timeout_seconds):
        """
        The function waits until the given pump has finished calibration or
        until the timeout occurs.
        """
        timer = qmixbus.PollingTimer(timeout_seconds * 1000)
        result = False
        while (result == False) and not timer.is_expired():
            time.sleep(0.1)
            result = pump.is_calibration_finished()
        return result
    
    @staticmethod
    def wait_dosage_finished(pump, timeout_seconds):
        """
        The function waits until the last dosage command has finished
        until the timeout occurs.
        """
        timer = qmixbus.PollingTimer(timeout_seconds * 1000)
        message_timer = qmixbus.PollingTimer(500)
        result = True
        while (result == True) and not timer.is_expired():
            time.sleep(0.1)
            if message_timer.is_expired():
                print("Fill level: ", pump.get_fill_level())
                message_timer.restart()
            result = pump.is_pumping()
        return not result

if __name__ == "__main__":
    
    pump = Pump()
    pump.start_pump()
    
    pump.load_fluid(1500)
    time.sleep(3)
    pump.unload_fluid(1000, 25)
    