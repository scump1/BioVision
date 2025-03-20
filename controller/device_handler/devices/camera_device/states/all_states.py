
import gxipy as gx
import os
import datetime
import time
import cv2
from apscheduler.schedulers.background import BackgroundScheduler

from controller.device_handler.devices.arduino_device.arduino import Arduino
from controller.device_handler.devices.camera_device.states.abc_state_baseclass import State
from controller.device_handler.devices.mfc_device.mfc import MFC

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
            
            numpy_image = self.device.get_latest_image
            
            filename = f"EmptyCalibration.bmp"
            filepath = os.path.join(dir_path, filename)
            
            cv2.imwrite(filepath, numpy_image)
            
            self.data.add_data(self.data.Keys.EMPTY_CALIBRATION_IMAGE_PATH, filepath, self.data.Namespaces.MIXING_TIME)
                
        except Exception as e:
            self.logger.warning(f"Image capturing not working properly: {e}.")

class MTFilledCalibrationState(State):
    
    def run_logic(self):
        
        self.take_single_image()
        
    def take_single_image(self):
    
        try:
            dir_path = self.data.get_data(self.data.Keys.CURRENT_MIXINGTIME_FOLDER_CALIBRATION, namespace=self.data.Namespaces.MIXING_TIME)
            
            if not dir_path:
                return
           
            numpy_image = self.device.get_latest_image
            
            filename = f"FilledCalibration.bmp"
            filepath = os.path.join(dir_path, filename)
            
            cv2.imwrite(filepath, numpy_image)
            
            self.data.add_data(self.data.Keys.FILLED_CALIBRATION_IMAGE_PATH, filepath, self.data.Namespaces.MIXING_TIME)

                
        except Exception as e:
            self.logger.warning(f"Image capturing not working properly: {e}.")

class MTImagecaptureState(State):
    
    def run_logic(self):
        
        try:
            # Scheduler setup
            self.scheduler = BackgroundScheduler()
            
            self.overall_count = 0
            
            self.device.mt_await_capture_start_event.wait()
            self.start_img_cap(10, 1)
            
            while datetime.datetime.now() < self.runtime_target and not self.terminated:
                self.logger.info("Camera - Image Capturing working.")
                time.sleep(1)
                
        except Exception as e:
            self.logger.warning(f"Error in capturing image: {e}.")
        finally:
            self.terminate_img_cap()
        
    def start_img_cap(self, img_per_int: int, interval: int):

        path = self.data.get_data(self.data.Keys.CURRENT_MIXINGTIME_FOLDER_IMAGES, namespace=self.data.Namespaces.MIXING_TIME)
        
        self.scheduler.add_job(self.single_img_capture, 'interval', args=[img_per_int, path], seconds=interval)
        self.scheduler.start()

    def terminate_img_cap(self):
        
        if self.scheduler:
            self.scheduler.shutdown()
        
    def single_img_capture(self, img_per_int: int, path: str):
        
        while img_per_int > 0:
            
            start_time = time.time()
            
            numpy_image = self.device.get_latest_image
            
            filename = f"MT_Image_{self.overall_count}.bmp"
            filepath = os.path.join(path, filename)
            
            cv2.imwrite(filepath, numpy_image)

            self.overall_count += 1
            img_per_int -= 1
            
            processingtime = time.time() - start_time
            
            time.sleep((1-0.1)/32 - processingtime)
            
class LiveViewState(State):
    
    def run_logic(self):
        
        instance = self.data.get_data(self.data.Keys.LIVE_VIEW_STATE_FORM, self.data.Namespaces.DEFAULT)
        instance.live_view_state_entered.emit()
        
        self.logger.info("Camera is in live mode.")

        while not self.terminated:
            time.sleep(1)

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
            self.mfc_interrupt = False
            
            if interval >= 10:
                self.arduino = Arduino.get_instance()
                self.lightmode = self.data.get_data(self.data.Keys.CAMERA_LIGHTSWITCHING, self.data.Namespaces.MEASUREMENT)
            
                self.mfc = MFC.get_instance()
                self.mfc_interrupt = self.data.get_data(self.data.Keys.CAMERA_MASSFLOW_INTERRUPT, self.data.Namespaces.MEASUREMENT)
                
            # Synchronization
            self.device.await_capture_start_event.wait()

            # Scheduler setup
            # We actually use two parallel running jobs with one second offset here
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

        self.scheduler.add_job(self.single_img_capture, 'interval', args=[img_per_int], seconds=interval)
        self.scheduler.start()

    def terminate_img_cap(self):
        
        if self.scheduler:
            self.scheduler.shutdown(wait=False)

    def single_img_capture(self, img_per_int: int):
        """
        Captures a series of images. A variety of flags can be set for this function internally. 
        
        data.Keys.CAMERA_LIGHTSWITCHING -> For swapping light back on and off
        data.Keys.CAMERA_MASSFLOW_INTERRUPT -> Turn off massflow while image capture
        data.Keys.IMAGE_CAPTURE_AREA -> Enumerator for image cap area
        
        Args:
            img_per_int (int): How manz images in a series per capture interval
            
        Return:
            None
        """
        try:
          
            if self.mfc_interrupt:
                self.mfc.add_task(self.mfc.States.CLOSE_VALVE, 0)

                time.sleep(5)

            if self.lightmode:
                self.data.add_data(self.data.Keys.LIGHTMODE, True, self.data.Namespaces.MEASUREMENT)
                self.arduino.add_task(self.arduino.States.LIGHT_SWITCH_STATE, 0)
            
                time.sleep(3)

            img_count = 0
            formatted_time = datetime.datetime.now().strftime("%H_%M_%S")

            # Grabbing the area of iterest
            area_enum = self.data.get_data(self.data.Keys.AREA_OF_INTERST, self.data.Namespaces.CAMERA)
            
            if not area_enum == self.device.AreaOfInterest.ALL:
                x1, x2, y1, y2 = self.device.area_of_interests.get(area_enum, None)

            while img_per_int > 0:
                
                start_time = time.time()
                numpy_image = self.device.get_latest_image
                
                if not area_enum == self.device.AreaOfInterest.ALL:
                    numpy_image = numpy_image[x1:x2, y1:y2]
                
                filename = f"Image_{formatted_time}_{img_count}.bmp"
                filepath = os.path.join(self.path, filename)
                
                cv2.imwrite(filepath, numpy_image)
                
                self.res_man.register_resource(f"Image_{formatted_time}_{img_count}.bmp", filepath, space=self.resourcespace)

                img_count += 1
                img_per_int -= 1
                
                endtime = time.time()
                processingtime = endtime - start_time
                
                # This means we wait for the given Framerate 32 minus the actual time it took for the image and some residue per frame to return to scheduler
                time.sleep((1-0.1)/32 - processingtime) 
                                
            if self.lightmode:
                self.data.add_data(self.data.Keys.LIGHTMODE, False, self.data.Namespaces.MEASUREMENT)
                self.arduino.add_task(self.arduino.States.LIGHT_SWITCH_STATE, 0)
            
            if self.mfc_interrupt:
                # this automatically resets the latest airflow
                self.mfc.add_task(self.mfc.States.OPEN_VALVE, 0)
            
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
            
            raw_img = self.device.get_latest_image # Accessing the image property from the image_acquisiton_thread

            if raw_img is None:
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