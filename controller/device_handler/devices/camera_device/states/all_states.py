
import gxipy as gx
import os
import datetime
import time
import cv2
from apscheduler.schedulers.background import BackgroundScheduler

from controller.device_handler.devices.arduino_device.arduino import Arduino
from controller.device_handler.devices.camera_device.states.abc_state_baseclass import State

class MTEmptyCalibrationState(State):
    
    def run_logic(self):
        try:
            self.take_single_image()
        except Exception as e:
            self.logger.warning(f"Error in taking empty calibration image: {e}.")
        
    def take_single_image(self):
    
        try:
            dir_path = self.data.get_data(self.data.Keys.CURRENT_MIXINGTIME_FOLDER_CALIBRATION, namespace=self.data.Namespaces.MIXING_TIME)
            
            if not dir_path:
                return
            
            self.device.cam.stream_on()
            raw_img = self.device.cam.data_stream[0].get_image()
            
            if raw_img is not None:
                rgb_image = raw_img.convert("RGB")
                numpy_image = rgb_image.get_numpy_array()
                numpy_image = numpy_image
                
                filename = f"EmptyCalibration.bmp"
                filepath = os.path.join(dir_path, filename)
                
                cv2.imwrite(filepath, numpy_image)
                
                self.data.add_data(self.data.Keys.EMPTY_CALIBRATION_IMAGE_PATH, filepath, self.data.Namespaces.MIXING_TIME)
                
            else:
                self.logger.warning("Failed to capture image: No data received from capture stream.")
                
        except Exception as e:
            self.logger.warning(f"Image capturing not working properly: {e}.")
            
        finally:
            self.device.cam.stream_off()

class MTFilledCalibrationState(State):
    
    def run_logic(self):
        
        self.take_single_image()
        
    def take_single_image(self):
    
        try:
            dir_path = self.data.get_data(self.data.Keys.CURRENT_MIXINGTIME_FOLDER_CALIBRATION, namespace=self.data.Namespaces.MIXING_TIME)
            
            if not dir_path:
                return
            
            self.device.cam.stream_on()
            raw_img = self.device.cam.data_stream[0].get_image()
            
            if raw_img is not None:
                rgb_image = raw_img.convert("RGB")
                numpy_image = rgb_image.get_numpy_array()
                numpy_image = numpy_image
                
                filename = f"FilledCalibration.bmp"
                filepath = os.path.join(dir_path, filename)
                
                cv2.imwrite(filepath, numpy_image)
                
                self.data.add_data(self.data.Keys.FILLED_CALIBRATION_IMAGE_PATH, filepath, self.data.Namespaces.MIXING_TIME)
                
            else:
                self.logger.warning("Failed to capture image: No data received from capture stream.")
                
        except Exception as e:
            self.logger.warning(f"Image capturing not working properly: {e}.")
            
        finally:
            self.device.cam.stream_off()

class MTImagecaptureState(State):
    
    def run_logic(self):
        
        try:
            # Scheduler setup
            self.scheduler = BackgroundScheduler()
            
            self.overall_count = 0
            
            self.device.mt_await_capture_start_event.wait()
            self.start_img_cap(6, 1)
            
            while datetime.datetime.now() < self.runtime_target and not self.terminated:
                self.logger.info("Camera - Image Capturing working.")
                time.sleep(1)
                
        except Exception as e:
            self.logger.warning(f"Error in capturing image: {e}.")
        finally:
            self.terminate_img_cap()
        
    def start_img_cap(self, img_per_int: int, interval: int):
        
        # First we open up the cam stream
        self.device.cam.stream_on()
        
        path = self.data.get_data(self.data.Keys.CURRENT_MIXINGTIME_FOLDER_IMAGES, namespace=self.data.Namespaces.MIXING_TIME)
        
        self.scheduler.add_job(self.single_img_capture, 'interval', args=[img_per_int, path], seconds=interval)
        self.scheduler.start()

    def terminate_img_cap(self):
        
        if self.scheduler:
            self.scheduler.shutdown()
            
        self.device.cam.stream_off()
        
    def single_img_capture(self, img_per_int: int, path: str):
        
        self.logger.info("Trying to capture Image.")

        while img_per_int > 0:
            raw_img = self.device.cam.data_stream[0].get_image()
            
            if raw_img is not None:
                rgb_image = raw_img.convert("RGB")
                numpy_image = rgb_image.get_numpy_array()
                numpy_image = numpy_image
                
                filename = f"MT_Image_{self.overall_count}.bmp"
                filepath = os.path.join(path, filename)
                
                cv2.imwrite(filepath, numpy_image)

            else:
                self.logger.warning("Failed to capture image: No data received from capture stream.")
                
            self.overall_count += 1
            img_per_int -= 1

class LiveViewState(State):
    
    def run_logic(self):
        
        self.events.trigger_event(self.events.EventKeys.LIVE_VIEW_STATE_ENTERED) # This signals the form that iut can grab the camera
        
        while self.device.task_queue.empty() and not self.terminated:
            self.logger.info("Camera is in live mode.")
            time.sleep(1)

        self.events.trigger_event(self.events.EventKeys.LIVE_VIEW_STATE_TERMINATED) # As soon as this state terminates the form terminates its access to the camera

class CalibrationImageState(State):
    """DEPRECEATED DO NOT USE"""
    def run_logic(self):
        
        calibpath = self.data.get_data(self.data.Keys.CURRENT_SLOT_FOLDER_CALIBRATION, namespace=self.data.Namespaces.MEASUREMENT)
        self.single_img_capture(1, calibpath)
        
    def single_img_capture(self, img_per_int: int, path: str):
        
        try:
            img_count = 0
            formatted_time = datetime.datetime.now().strftime("%H_%M_%S")
            
            self.device.cam.stream_on()

            while img_per_int > 0:
                raw_img = self.device.cam.data_stream[0].get_image()
                if raw_img is not None:
                    rgb_image = raw_img.convert("RGB")
                    numpy_image = rgb_image.get_numpy_array()
                    numpy_image = numpy_image[600:2500, 1800:2175]
                    
                    filename = f"Image_{formatted_time}_{img_count}.bmp"
                    filepath = os.path.join(path, filename)

                    cv2.imwrite(filepath, numpy_image)
                    
                    # We want to only have one image in this space at all times
                    self.data.add_data(self.data.Keys.CALIBRATION_IMAGE_PATH, filepath, self.data.Namespaces.MEASUREMENT)

                else:
                    self.logger.warning("Failed to capture image: No data received from capture stream.")
                    
                img_count += 1
                img_per_int -= 1
                    
        except Exception as e:
            self.logger.warning(f"Image capturing not working properly: {e}.")
            
        finally:
            self.device.cam.stream_off()

class ImageCaptureState(State):
    
    def run_logic(self):
        
        try:                
            # Setup            
            settings = self.data.get_data(self.data.Keys.CAMERA_SETTINGS, namespace=self.data.Namespaces.CAMERA)
            img_per_int, interval = settings
            self.path = self.data.get_data(self.data.Keys.CURRENT_SLOT_FOLDER_IMAGES, namespace=self.data.Namespaces.MEASUREMENT)
                
            self.resourcespace = self.data.get_data(self.data.Keys.CURRENT_RESOURCE_SPACE, namespace=self.data.Namespaces.MEASUREMENT)
            
            # Safety check for the interval light siwtching -> only possible when more than 5 seconds intervals
            self.lightmode = False
            if interval >= 5:
                self.arduino = Arduino.get_instance()
                self.lightmode = self.data.get_data(self.data.Keys.CAMERA_LIGHTSWITCHING, self.data.Namespaces.MEASUREMENT)
        
            # Synchronization
            self.device.await_capture_start_event.wait()

            # Scheduler setup
            self.scheduler = BackgroundScheduler()

            self.start_img_cap(img_per_int, interval)
            
            while datetime.datetime.now() < self.runtime_target and not self.terminated:
                self.logger.info("Camera - Image Capturing working.")
                time.sleep(1)
                
        except Exception as e:
            self.logger.warning(f"Error in capturing image: {e}.")
        finally:    
            self.terminate_img_cap()

    def start_img_cap(self, img_per_int, interval):
        
        # First we open up the cam stream
        self.device.cam.stream_on()
        
        self.scheduler.add_job(self.single_img_capture, 'interval', args=[img_per_int], seconds=interval)
        self.scheduler.start()

    def terminate_img_cap(self):
        
        if self.scheduler:
            self.scheduler.shutdown()
            
        self.device.cam.stream_off()

    def single_img_capture(self, img_per_int: int):
        
        try:
            if self.lightmode:
                self.data.add_data(self.data.Keys.LIGHTMODE, True, self.data.Namespaces.MEASUREMENT)
                self.arduino.add_task(self.arduino.States.LIGHT_SWITCH_STATE, 0)

                time.sleep(3)
            
            img_count = 0
            formatted_time = datetime.datetime.now().strftime("%H_%M_%S")
            self.logger.info("Trying to capture Image")

            while img_per_int > 0:
                raw_img = self.device.cam.data_stream[0].get_image()
                
                if raw_img is not None:
                    rgb_image = raw_img.convert("RGB")
                    numpy_image = rgb_image.get_numpy_array()
                    numpy_image = numpy_image[600:2500, 1800:2175]
                    
                    filename = f"Image_{formatted_time}_{img_count}.bmp"
                    filepath = os.path.join(self.path, filename)
                    
                    cv2.imwrite(filepath, numpy_image)
                    
                    self.res_man.register_resource(f"Image_{formatted_time}_{img_count}.bmp", filepath, space=self.resourcespace)

                else:
                    self.logger.warning("Failed to capture image: No data received from capture stream.")
                    
                img_count += 1
                img_per_int -= 1
            
            if self.lightmode:
                self.data.add_data(self.data.Keys.LIGHTMODE, False, self.data.Namespaces.MEASUREMENT)
                self.arduino.add_task(self.arduino.States.LIGHT_SWITCH_STATE, 0)
            
        except Exception as e:
            self.logger.warning(f"Image capturing not working properly: {e}.")
                
class HealthCheckState(State):
    
    def run_logic(self):
        
        self.health_check()

    def check_device(self) -> bool:
        
        try:
            if not self.device.cam:
                self.data.add_data(self.data.Keys.CAMERA, False, namespace=self.data.Namespaces.DEVICES)
                return False      
            
            self.device.cam.stream_on() 
            raw_img = self.device.cam.data_stream[0].get_image()
            self.device.cam.stream_off()

            if not raw_img:
                self.data.add_data(self.data.Keys.CAMERA, False, namespace=self.data.Namespaces.DEVICES)
                return False
            
            self.data.add_data(self.data.Keys.CAMERA, True, namespace=self.data.Namespaces.DEVICES)

            del raw_img
            return True
            
        except Exception as e:
            self.logger.error(f"Unexpected error in health check: {e}")
            self.data.add_data(self.data.Keys.CAMERA, False, namespace=self.data.Namespaces.DEVICES)
            return False

    def health_check(self):

        if self.device.cam:
            
            if not self.check_device():
                
                self.device._connect()
                
                _ = self.check_device()
            
        elif not self.device.cam:
            self.device._connect()
            
            _ = self.check_device()

class SetSettingsState(State):
    
    def run_logic(self):
        
        self.set_camera_settings()
    
    def set_camera_settings(self):
        
        # Grab the Settings HERE
        settings = self.data.get_data(self.data.Keys.CAMERA_DEVICE_SETTINGS, self.data.Namespaces.CAMERA)
        autowhite_balance, exposuretime, gain, saturation = settings

        # Set the settings if valid - we can only change the numeral values
        if self.device:
            self.settings = {

                self.device.cam.AcquisitionMode : gx.GxAcquisitionModeEntry.CONTINUOUS,
                self.device.cam.BalanceWhiteAuto: autowhite_balance,
                self.device.cam.ExposureTime: exposuretime,
                self.device.cam.GammaMode: gx.GxGammaModeEntry.SRGB,
                self.device.cam.PixelFormat: gx.GxPixelFormatEntry.BAYER_RG12,
                self.device.cam.GainAuto: gx.GxAutoEntry.OFF,
                self.device.cam.Gain: gain,
                self.device.cam.SaturationMode: 1,
                self.device.cam.Saturation: saturation,
                self.device.cam.BalanceRatioSelector: gx.GxBalanceRatioSelectorEntry.RED
                            }

            for key in self.settings.keys():
                if key.is_implemented() and key.is_writable():
                    key.set(self.settings[key])
                    self.logger.info(f"Set {key} to camera succesfully.")
                    
                else:
                    self.logger.warning(f"Setting {key} to camera unsuccesful.")
        else:
            self.logger.error("Error in setting non-default settings.")
        
        if exposuretime == self.device.cam.ExposureTime.get() and autowhite_balance == list(self.device.cam.BalanceWhiteAuto.get())[0] and gain == self.device.cam.Gain.get() and saturation == self.device.cam.Saturation.get():
            self.data.add_data(self.data.Keys.CAMERA_DEVICE_SETTINGS_SUCCESS, True, self.data.Namespaces.CAMERA)
            
        else:
            self.data.add_data(self.data.Keys.CAMERA_DEVICE_SETTINGS_SUCCESS, False, self.data.Namespaces.CAMERA)