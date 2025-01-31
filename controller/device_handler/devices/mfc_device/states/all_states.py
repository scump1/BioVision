
import math
import time
from controller.device_handler.devices.mfc_device.states.abc_state_baseclass import State
            
class HealthCheckState(State):
    
    def run_logic(self):
        
        self.health_check()
    
    def check_device(self) -> bool:
        
        if self.device.mfc_instrument:    
            read = self.device.mfc_instrument.readParameter(205)
            
            if read is not None:
                self.data.add_data(self.data.Keys.MFC, True, namespace=self.data.Namespaces.DEVICES)
                return True
  
        self.data.add_data(self.data.Keys.MFC, False, namespace=self.data.Namespaces.DEVICES)
        return False
          
    def health_check(self):
        
        try:
            check = self.check_device()
            if check is False:
                # Here we try reconnecting
                self.device._connect()
                
                _ = self.check_device()
                
        except Exception as e:
            self.logger.error(f"Device not healthy: {e}.")
            self.data.add_data(self.data.Keys.MFC, False, namespace=self.data.Namespaces.DEVICES)
            
class SettingsSetter(State):
    
    def run_logic(self):
        
        try:
            massflow = self.data.get_data(self.data.Keys.MFC_SETTINGS, namespace=self.data.Namespaces.MFC)
            
            print(f"MASSFLOW: {massflow}")
            if not massflow:
                self.data.add_data(self.data.Keys.MFC_SETTINGS_SUCCESS, False, self.data.Namespaces.MFC)
                return
            
            massflow = float(massflow)
            self.device.mfc_instrument.writeParameter(206, massflow)

            time.sleep(0.5)
            read = self.device.mfc_instrument.readParameter(205)
            print(f"READ MASSFLOW: {read}")
            if abs(read - massflow) < 2.5:
                self.data.add_data(self.data.Keys.MFC_SETTINGS_SUCCESS, True, self.data.Namespaces.MFC)
            else:
                self.data.add_data(self.data.Keys.MFC_SETTINGS_SUCCESS, False, self.data.Namespaces.MFC)
            
        except Exception as e:
            self.logger.error(f"Error in writing to Instrument: {e}")
            
class PollingState(State):
    
    def run_logic(self):
    
        self.poll_mfc()
    
    def poll_mfc(self):
        
        try:
            read = self.device.mfc_instrument.readParameter(205)
            
            if read is not None:
                self.data_writer.mfc_data_writer(read)
                
        except Exception as e:
            self.logger.error(f"Could not read values: {e}.")
            
class ReadMassFlowState(State):
    
    def run_logic(self):
        
        self.reader()
        
    def reader(self):
        
        try:
            read = self.device.mfc_instrument.readParameter(205)
            # unit = self.device.mfc_insturment.readParameter(129)
            
            if read is not None:
                self.data.add_data(self.data.Keys.MFC_MASSFLOW, read, self.data.Namespaces.MFC)
                
        except Exception as e:
            self.logger.error(f"Could not read values: {e}.")

class AirflowValveSwitch(State):
    
    def run_logic(self):
        
        self.switch_valve()
        
    def switch_valve(self):
        
        try:
            read = self.device.mfc_instrument.readParameter(205)

            # this means that we have an "open" valve
            if read is not None and read > 0.0:
                self.logger.info("Shutting down airflow shortly.")
                self.device.mfc_instrument.writeParameter(206, 0.0)
            
            # This means valve is closed
            elif math.isclose(read, 0.0, abs_tol=1e-5):
                self.logger.info("Reopening airflow.")
                # Trying to retriveve the last massflow setting
                massflow = self.data.get_data(self.data.Keys.MFC_SETTINGS, namespace=self.data.Namespaces.MFC)
                
                if massflow is not None:
                    self.device.mfc_instrument.writeParameter(206, massflow)
                else:
                    self.device.mfc_instrument.writeParameter(206, 5.0)
        
        except Exception as e:
            self.logger.warning(f"Could not switch valve: {e}.")