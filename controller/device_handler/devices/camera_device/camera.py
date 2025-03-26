
import threading
import time
import copy

import gxipy as gx

from enum import Enum

from controller.device_handler.devices.camera_device.states.all_states import HealthCheckState, ImageCaptureState, LiveViewState, SetSettingsState, MTEmptyCalibrationState, MTFilledCalibrationState, MTImagecaptureState
from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from model.data.configuration_manager import ConfigurationManager
from operator_mod.logger.global_logger import Logger

from controller.device_handler.devices.state_machine_template import Device

class Camera(Device):
        
    _instance = None
    _lock = threading.Lock()
    _image_lock = threading.Lock()
    
    FRAMES_PER_SECOND : int = 10
    
    # Exposing the enums to the outside
    class States(Enum):
        HEALTH_CHECK_STATE = 1
        IMAGE_CAPTURE_STATE = 2
        LIVE_VIEW_STATE = 3
        CALIBRATION_IMAGE_STATE = 4
        CUSTOM_SETTINGS_SETTER = 5
        MT_EMPTY_CALIBRATION_STATE = 6
        MT_FILLED_CALIBRATION_STATE = 7
        MT_IMAGE_CAPTURE_STATE = 8
    
    state_classes = {
        States.HEALTH_CHECK_STATE: HealthCheckState,
        States.IMAGE_CAPTURE_STATE: ImageCaptureState,
        States.LIVE_VIEW_STATE: LiveViewState,
        States.CUSTOM_SETTINGS_SETTER: SetSettingsState,
        States.MT_EMPTY_CALIBRATION_STATE: MTEmptyCalibrationState,
        States.MT_FILLED_CALIBRATION_STATE: MTFilledCalibrationState,
        States.MT_IMAGE_CAPTURE_STATE: MTImagecaptureState
        # Add more states here
    }
    
    # Exposing the Enum to the outside
    class AreaOfInterest(Enum):
        
        ALL = 0
        
        COLUMN = 1
        COLUMN_WITH_TOP = 2
        
    area_of_interests = {
        AreaOfInterest.ALL: [],
        AreaOfInterest.COLUMN: [600, 2500, 1700, 2100],
        AreaOfInterest.COLUMN_WITH_TOP: [600, 3000, 1600, 2200]
    }

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Camera, cls).__new__(cls)
        return cls._instance

    def __init__(self):
    
        super().__init__()
    
        # utils
        self.logger = Logger("Camera").logger
        self.data = InMemoryData()
        self.configurations = ConfigurationManager.get_instance()
        
        # Standard Value
        self.data.add_data(self.data.Keys.AREA_OF_INTERST, self.AreaOfInterest.COLUMN, self.data.Namespaces.CAMERA)
        
        # The camera device
        self.cam = None
        
        # Threading events
        self.await_capture_start_event = threading.Event()
        self.mt_await_capture_start_event = threading.Event()
        
        self.latest_image = None
        self.new_frame_image = None
        
        self._connect()
        self.setupCamera()

        self.image_acqusition_running = True # Only sets to False in __del__
        
        self.image_acquisition_thread = threading.Thread(target=self.image_acqusition_thread_worker)
        self.image_acquisition_thread.daemon = True
        self.image_acquisition_thread.start()

    def __del__(self):
        
        if self.image_acquisition_thread.is_alive():
            self.image_acqusition_running = False
            self.image_acquisition_thread.join()
            
        self.shutdown()

    ### Camera logic ###
    def _connect(self):
        """Tries to establish a connection to the device."""
        try:
            # Camera Manager via SDK
            self.cam_manager = gx.DeviceManager()

            if self.cam is None:
                self.cam = self.cam_manager.open_device_by_sn("FCU23120403")

            if self.cam is not None:
                self.data.add_data(self.data.Keys.CAMERA, True, namespace=self.data.Namespaces.DEVICES)
                self.logger.info("Camera operable.")

            else:
                self.data.add_data(self.data.Keys.CAMERA, False, namespace=self.data.Namespaces.DEVICES)
                self.logger.info("Not connected.")
                
        except Exception as e:
            self.data.add_data(self.data.Keys.CAMERA, False, namespace=self.data.Namespaces.DEVICES)
            self.logger.warning(f"Could not connect to camera in health check: {e}")
        
    def setupCamera(self):

        if self.cam:
                            
            # Here we unravel the settings
            settings = self.configurations.get_configuration(self.configurations.Devices.CAMERA)   
            camsetting = list(settings.values())

            self.settings = {

                self.cam.AcquisitionMode : gx.GxAcquisitionModeEntry.CONTINUOUS,
                self.cam.SensorShutterMode : gx.GxSensorShutterModeEntry.ROLLING,
                self.cam.BalanceWhiteAuto: camsetting[0],
                self.cam.ExposureTime: camsetting[1],
                self.cam.GammaMode: gx.GxGammaModeEntry.SRGB,
                self.cam.PixelFormat: gx.GxPixelFormatEntry.BAYER_RG12,
                self.cam.PixelColorFilter: gx.GxPixelColorFilterEntry.BAYER_RG,
                self.cam.PixelSize: gx.GxPixelSizeEntry.BPP12,
                self.cam.GainAuto: gx.GxAutoEntry.OFF,
                self.cam.Gain: camsetting[2],
                self.cam.SaturationMode: 0,
                self.cam.Saturation: camsetting[3],
                self.cam.BalanceRatioSelector: gx.GxBalanceRatioSelectorEntry.RED
                            }

            for key in self.settings.keys():
                if key.is_implemented() and key.is_writable():
                    key.set(self.settings[key])
                    self.logger.info(f"Set {key} to camera succesfully.")
                else:
                    self.logger.info(f"Setting {key} is not writable.")
        else:
            self.logger.error("Not connected.")
    
    ### Seperate image acquisiton thread to offload saving/writing image files from the image acqusition loop
    def image_acqusition_thread_worker(self):
        
        # Start the image stream
        if self.cam is None:
            self.logger.error("No camera connected.")
            return
        
        self.cam.stream_on()

        while self.image_acqusition_running:
            try:
                image = self.cam.data_stream[0].get_image()
                
                if image is not None:
                    image = image.convert('RGB')
                    new_frame = image.get_numpy_array()
                
                    with self._image_lock:
                        self.latest_image = new_frame

            except:
                self.logger.warning('Error in image acquisiton thread, image skipped.')
                
        self.cam.stream_off()

    @property
    def get_latest_image(self):
        with self._image_lock:
            return self.latest_image
    
    @property
    def get_camera(self):
        with self._lock:
            return self.cam
