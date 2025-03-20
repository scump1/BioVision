
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
            
            if not massflow:
                self.data.add_data(self.data.Keys.MFC_SETTINGS_SUCCESS, False, self.data.Namespaces.MFC)
                return
            
            massflow = float(massflow)
            self.device.mfc_instrument.writeParameter(206, massflow)

            self.data.add_data(self.data.Keys.MFC_SETTINGS_SUCCESS, True, self.data.Namespaces.MFC)
            
            reference = self.data.get_data(self.data.Keys.MFC_DEVICE_UI_REFERENCE, self.data.Namespaces.PROJECT_MANAGEMENT)
            
            if reference is not None:
                reference.massflow_set.emit()
            
            
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

class CloseValve(State):
    
    def run_logic(self):
        
        try:
            ## Actually closing
            self.device.mfc_instrument.writeParameter(206, 0.0)

        except Exception as e:
            self.logger.warning(f"Could not close valve: {e}.")
        
class OpenValve(State):
    
    def run_logic(self):
        
        try:
            # Trying to get the latest read
            massflow = self.data.get_data(self.data.Keys.MFC_SETTINGS, self.data.Namespaces.MFC)
            
            if massflow is not None:
                self.device.mfc_instrument.writeParameter(206, float(massflow))
            else:
                self.device.mfc_instrument.writeParameter(206, 5.0)
        
        except Exception as e:
            self.logger.warning(f"Could not open valve with latest read: {massflow}, {e}.")