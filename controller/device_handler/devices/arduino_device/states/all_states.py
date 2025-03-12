
import time
import datetime
import serial

from apscheduler.schedulers.background import BackgroundScheduler

from controller.device_handler.devices.arduino_device.states.abc_state_baseclass import State

class SettingsSetterState(State):
    
    def run_logic(self):
        
        try:
            temperature = self.data.get_data(self.data.Keys.TEMPERATURE_SETTING, self.data.Namespaces.ARDUINO)
            live_record = self.data.get_data(self.data.Keys.LIVE_RECORDING, self.data.Namespaces.ARDUINO)
            
            if not type(temperature) == float:
                self.logger.error(f"Arduino - Could not get target temperature: {e}")
                return
                                
            self.setsettings(temperature, live_record)
        
        except Exception as e:
            self.logger.error(f"Arduino - Could not get target temperature: {e}")
            return

    def setsettings(self, temperature: float, live_record: bool):

        # Checking the live recorder
        self.live_recording = live_record

        if self.device.serial_con:
            try:
                # Send the temperature command
                self.device.send_command("T")
                response = self.device.send_command(str(temperature))
                
                self.logger.info(f"Sent command: T with temperature {temperature}.")

                if response[0] == str(temperature):
                    self.logger.info("Temperature setting set.")
                else:
                    self.logger.warning(f"Unexpected response: {response}.")

            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                self.data.add_data(self.data.Keys.ARDUINO, False, namespace=self.data.Namespaces.DEVICES)
        else:
            self.logger.error("Arduino is not connected.")

class SensorPolling(State):
    
    def run_logic(self):
        
        self.sched = BackgroundScheduler()
        
        # Synchronization
        self.device.await_polling_start_event.wait()
        
        if self.device.serial_con:
            self.sched.add_job(self._polling, trigger='interval', seconds=15)
            self.sched.start()

        while datetime.datetime.now() < self.runtime_target and not self.terminated:
            time.sleep(1)

        # This is the final code
        self.sched.pause()
        self.sched.remove_all_jobs()
        self.sched.shutdown(wait=False)

        del self.sched

    def _polling(self):
        
        try:
            response = self.device.send_command("R") # Request data from Arduino
            
            if response:
                self.data_writer.arduino_data_writer(response)
                if self.live_recording:
                    self.data.add_data(self.data.Keys.LIVE_TEMPERATURE, response, self.data.Namespaces.MEASUREMENT)
                
        except Exception as e:
            self.logger.error(f"Arduino - Error in polling sensors: {e}")

class LightSwitch(State):
    
    def run_logic(self):
        
        if self.device.serial_con:
            try:
                
                lightmode = self.data.get_data(self.data.Keys.LIGHTMODE, self.data.Namespaces.MEASUREMENT)
                position : int = None

                if lightmode == False:
                    position : int = 0
                elif lightmode == True:
                    position : int = 1
                      
                else:
                    self.logger.critical("Arduino light state not boolean.")
                    return    
                                                     
                if position is not None:
                    _ = self.device.send_command("S")
                    _ = self.device.send_command(str(position))
                    
                else:
                    self.logger.warning("Tried to write [None] position to light switch.")
                
            except Exception as e:
                self.logger.error(f"Error in setting light switch: {e}.")
                
        else:
            self.logger.error("Arduino not connected.")

class HealthCheckState(State):
    
    def run_logic(self):
        
        self.health_check()
        
    def check_device(self):
        
        try:
            
            if self.device.serial_con is None:
                self.data.add_data(self.data.Keys.ARDUINO, False, namespace=self.data.Namespaces.DEVICES)
                return False
            
            response = self.device.send_command("H")

            if response[0] == "Y":
                self.data.add_data(self.data.Keys.ARDUINO, True, namespace=self.data.Namespaces.DEVICES)
                self.logger.info("Arduino operable.")
                return True
            else:
                self.logger.error("Arduino not operable.")

        except serial.SerialException as e:
            self.logger.error(f"Serial error in health check: {e}")
            self.data.add_data(self.data.Keys.ARDUINO, False, namespace=self.data.Namespaces.DEVICES)
        except Exception as e:
            self.logger.error(f"Unexpected error in health check: {e}")
            self.data.add_data(self.data.Keys.ARDUINO, False, namespace=self.data.Namespaces.DEVICES)
        finally:
            if self.device.serial_con is not None:
                self.device.serial_con.flush()
        
        return False
    
    def health_check(self):

        if self.device.serial_con:
            
            if self.check_device():
                return
            
            else:
                self.device._connect()
                
                if self.check_device():
                    return

        elif not self.device.serial_con:
            self.device._connect()
        
            _ = self.check_device()
        
        else:
            self.data.add_data(self.data.Keys.ARDUINO, False, namespace=self.data.Namespaces.DEVICES)