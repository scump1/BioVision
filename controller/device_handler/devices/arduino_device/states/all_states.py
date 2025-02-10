
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
                self.device.serial_con.write("T\n".encode())
                self.device.serial_con.write(f"{temperature}\n".encode())
                self.logger.info(f"Sent command: T with temperature {temperature}.")

                if self._wait_for_response(expected_response=temperature):
                    self.logger.info("Temperature setting set.")
                else:
                    self.logger.warning(f"Failed to set temperature setting. Expected response: {temperature}.")

            except serial.SerialException as e:
                self.logger.error(f"Serial error: {e}")
                self.data.add_data(self.data.Keys.ARDUINO, False, namespace=self.data.Namespaces.DEVICES)
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
            self.logger.info("Arduino Working")
            time.sleep(1)

        # This is the final code
        self.sched.pause()
        self.sched.remove_all_jobs()
        self.sched.shutdown()

        del self.sched

    def _polling(self):
        
        try:
            self.device.serial_con.write('R\n'.encode())  # Request data from Arduino
            time.sleep(0.5)
            
            ard_data = []
            i = 3
            while i > 0 and not self.terminated:
                if self.device.serial_con.in_waiting > 0:
                    read = self.device.serial_con.readline().decode().strip()
                    ard_data.append(read)
                    i -= 1

            # Data adding logic
            if ard_data:
                self.data_writer.arduino_data_writer(ard_data)
                if self.live_recording:
                    self.data.add_data(self.data.Keys.LIVE_TEMPERATURE, ard_data[0], self.data.Namespaces.MEASUREMENT)
                
        except Exception as e:
            self.logger.error(f"Arduino - Error in polling sensors: {e}")

class LightSwitch(State):
    
    def run_logic(self):
        
        if self.device.serial_con:
            try:
                
                lightmode = self.data.get_data(self.data.Keys.LIGHTMODE, self.data.Namespaces.MEASUREMENT)
                position = None
                
                if lightmode == False:
                    position = 0
                elif lightmode == True:
                    position = 1
                    
                else:
                    return    
                
                self.device.serial_con.write('S\n'.encode())
                self.device.serial_con.write(f"{position}\n".encode())
                
                if self._wait_for_response(expected_response=position):
                    self.logger.info("Light switch set.")
                else:
                    self.logger.warning(f"Unexpected response: {position}.")
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
            
            self.device.serial_con.write("H\n".encode())
            if self._wait_for_response():
                self.logger.info("Arduino healthy and connected.")
                self.data.add_data(self.data.Keys.ARDUINO, True, namespace=self.data.Namespaces.DEVICES)
                return True
            
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
            
            if not self.check_device():
                self.device._connect()
            
            _ = self.check_device()

        elif not self.device.serial_con:
            self.device._connect()
        
            _ = self.check_device()
        
        else:
            self.data.add_data(self.data.Keys.ARDUINO, False, namespace=self.data.Namespaces.DEVICES)