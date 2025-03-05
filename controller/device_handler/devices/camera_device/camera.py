
import threading

import gxipy as gx

from enum import Enum

from controller.device_handler.devices.camera_device.states.all_states import HealthCheckState, ImageCaptureState, LiveViewState, CalibrationImageState, SetSettingsState, MTEmptyCalibrationState, MTFilledCalibrationState, MTImagecaptureState
from operator_mod.in_mem_storage.in_memory_data import InMemoryData
from model.data.configuration_manager import ConfigurationManager
from operator_mod.logger.global_logger import Logger

from controller.device_handler.devices.state_machine_template import Device

class Camera(Device):
    
    _instance = None
    _lock = threading.Lock()
    
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
        States.CALIBRATION_IMAGE_STATE: CalibrationImageState,
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
        AreaOfInterest.COLUMN: [600, 2500, 1700, 2175],
        AreaOfInterest.COLUMN_WITH_TOP: [600, 3000, 1700, 2175]
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
        self.data.add_data(self.data.Keys.AREA_OF_INTERST, self.AreaOfInterest.ALL, self.data.Namespaces.CAMERA)
        
        # The camera device
        self.cam = None
        
        # Threading events
        self.await_capture_start_event = threading.Event()
        self.mt_await_capture_start_event = threading.Event()
        
        self._connect()
        self.setupCamera()

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
    
    @property
    def get_camera(self):
        with self._lock:
            return self.cam
