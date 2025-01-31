
from controller.device_handler.devices.pump_device.states.abc_state_baseclass import State


class HealthCheckState(State):
    
    def run_logic(self):
        self.health_check()
    
    def check_device(self):
        
        if self.device.pump:
            enabled = self.device.pump.is_enabled()
            
            if enabled:
                self.data.add_data(self.data.Keys.PUMP, True, namespace=self.data.Namespaces.DEVICES)
                return True
            else:
                self.data.add_data(self.data.Keys.PUMP, False, namespace=self.data.Namespaces.DEVICES)
                return False
    
    def health_check(self):
        
        try:
            check = self.check_device()
            
            if check is False:
                self.device._connect()
                self.device._start_pump()
            
                _ = self.check_device()
            
        except Exception as e:
            self.data.add_data(self.data.Keys.PUMP, False, namespace=self.data.Namespaces.DEVICES)
            self.logger.warning(f"Error in health check: {e}")
            
class LoadFluidState(State):
    
    def run_logic(self):
        
        volume = self.data.get_data(self.data.Keys.PUMP_LOAD_VOLUME, namespace=self.data.Namespaces.PUMP)

        self.device.load_fluid(volume)
        
class UnloadFluidState(State):
    
    def run_logic(self):
        
        volume = self.data.get_data(self.data.Keys.PUMP_UNLOAD_VOLUME, namespace=self.data.Namespaces.PUMP)
        flow = self.data.get_data(self.data.Keys.PUMP_FLOW, namespace=self.data.Namespaces.PUMP)
        
        if flow is None or flow == 0:
            flow = self.device.max_flowrate
        
        self.device.unload_fluid(volume, flow)
        
class MTUnloadFluidState(State):
    
    def run_logic(self):
        
        volume = self.data.get_data(self.data.Keys.PUMP_UNLOAD_VOLUME, namespace=self.data.Namespaces.PUMP)
        
        self.device.await_mt_injection_event.wait()
        self.device.unload_fluid(volume, self.device.max_flowrate)