
from controller.device_handler.device_handler_class.states.state_baseclass import State
            
class HealthCheckState(State):
    
    def run_logic(self):
        
        self.health_check()
        
    def health_check(self):

        try:
            # We only check health if no measurement is running (the devices aren't busy)
            if not self.data.get_data(self.data.Keys.MEASUREMENT_RUNNING, namespace=self.data.Namespaces.MEASUREMENT):

                connected = []
                
                for key in self.device_handler.devices.keys():
                    
                    status = self.data.get_data(self.device_handler.devices[key][0], namespace=self.data.Namespaces.DEVICES) 
                    
                    if status:
                        connected.append(key)
                    else:
                        self.device_handler.devices[key][1].add_task(self.device_handler.devices[key][1].States.HEALTH_CHECK_STATE, 0)

                self.data.add_data(self.data.Keys.CONNECTED_DEVICES, connected, namespace=self.data.Namespaces.CONTROLLER)            
        
        except Exception as e:
            self.logger.error(f"Device Handler - Health Check - Error occured: {e}")