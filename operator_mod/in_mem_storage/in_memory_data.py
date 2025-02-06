import copy
import uuid
import threading
import numpy as np
from enum import Enum

class InMemoryData:
    """
    InMemoryData is a thread-safe, in-memory data storage system that supports multiple namespaces 
    for segregating data across different parts of an application (e.g., GUI, controller). It also 
    supports tagging for easy sorting and retrieval of key variables across namespaces.

    This singleton class ensures that only one instance of the data storage exists and provides 
    methods to create, manage, and retrieve data within different namespaces.

    Methods:
    
        create_namespace(namespace):
            Creates a new namespace.

        delete_namespace(namespace):
            Deletes an existing namespace.

        add_data(keys, value, namespace="default", tags=None):
            Adds data to the specified namespace. Optionally labels the data with tags.

        get_data(key=None, namespace="default", uid=None):
            Retrieves data from the specified namespace by key or uid.

        delete_data(keys, namespace="default"):
            Deletes data associated with the provided keys from the specified namespace.

        remove_tags(uid, namespace, tags):
            Removes specified tags from a data entry identified by uid and namespace.

        get_data_by_tag(tag):
            Retrieves data entries across namespaces associated with the provided tag.

        purge_all_data(namespace="default"):
            Clears all data from the specified namespace.

        check_key(key, namespace="default"):
            Checks if a key exists in the specified namespace.

        list_namespaces():
            Lists all existing namespaces.

    Usage Examples:

        # Initialize and create namespaces
        data_store = InMemoryData()
        data_store.create_namespace("gui")
        data_store.create_namespace("controller")

        # Add data with tags to different namespaces
        data_store.add_data(["width", "height"], 600, namespace="gui", tags=["dimension"])
        data_store.add_data("speed", 120, namespace="controller", tags=["motor"])

        # Retrieve data by key
        width = data_store.get_data("width", namespace="gui")
        speed = data_store.get_data("speed", namespace="controller")

        # Retrieve data by tag
        dimension_data = data_store.get_data_by_tag("dimension")

        # Delete data
        data_store.delete_data(["width", "height"], namespace="gui")

        # Purge all data from a namespace
        data_store.purge_all_data(namespace="controller")
    """
    
    # These are automatically generated
    class Keys(Enum):
        # Devices
        ARDUINO = "Arduino"
        CAMERA = "Camera"
        PUMP = "Pump"
        MFC = "MFC"
        FIRESTING = "Firesting"
                
        CONNECTED_DEVICES = "ConnectedDevices"
        
        # PUMP
        PUMP_UNLOAD_VOLUME = "PumpUnloadVolume"
        PUMP_LOAD_VOLUME = "PumpVolume"
        PUMP_FLOW = "PumpFlow"
        
        SYRINGE_DIAMETER = "SyringeDiameter"
        SYRINGE_LENGTH = "SyringeLength"
        
        # MFC
        MFC_MASSFLOW = 'MFCMassflow'
        MFC_SETTINGS_SUCCESS = 'MFCSettingsSuccess'
        
        # Measurement
        MEASUREMENT_RUNNING = "MeasurementRunning"

        MEASUREMENT_STOPPED_AND_WAITING = "MSStoppedAndWaiting"

        CURRENT_RESOURCE_SPACE = "CurrentResourceSpace"
        CURRENT_MEASUREMENT_FOLDER = "CurrentMeasurementFolder"
        
        CURRENT_SLOT_FOLDER = "CurrentSlotFolder"
        CURRENT_SLOT_FOLDER_CALIBRATION = "CurrentSlotFolderCalibration"
        CURRENT_SLOT_FOLDER_RESULT = "CurrentSlotFolderResult"
        CURRENT_SLOT_FOLDER_IMAGES = "CurrentSlotFolderImages"
        CURRENT_SLOT_RESULT_DB = "CurrentResultDB"
        
        CALIBRATION_IMAGE_PATH = "CalibrationImagePath"
        LIVE_TEMPERATURE = "LiveTemperature"
        
        LIGHTMODE = "ArduinoLightmode"
        CAMERA_LIGHTSWITCHING = "CameraLightmode"
        
        # MIXING TIME
        CURRENT_MIXINGTIME_FOLDER = "CurrentMixingTimeFolder"
        
        CURRENT_MIXINGTIME_FOLDER_CALIBRATION = "CurrentMixingTimeFolderCalibration"
        CURRENT_MIXINGTIME_FOLDER_IMAGES = "CurrentMixingTimeFolderImages"
        CURRENT_MIXINGTIME_FOLDER_DATA = "CurrentMixingTimeFolderData"
        
        EMPTY_CALIBRATION_IMAGE_PATH = "EmptyCalibrationImagePath"
        FILLED_CALIBRATION_IMAGE_PATH = "FilledCalibrationImagePath"
        
        # Project Management
        PROJECT_FOLDER_CONFIG = "ProjectFolderConfig"
        PROJECT_FOLDER_MEASUREMENT = "ProjectFolderMeasurement"
        PROJECT_FOLDER_USERDATA = "ProjectFolderUserData"
        PROJECT_PATH = "ProjectPath"
        
        # Device Settings
        TEMPERATURE_SETTING = "TemperatureSetting"
        CAMERA_SETTINGS = "CameraSettings"
        PUMP_SETTING = "PumpSetting"
        MFC_SETTINGS = "MFCSettings"
        FIRESTING_SETTINGS = "FirestingSettings"
        
        # Live Data Write State
        LIVE_RECORDING = "EnvTemperature"
        
        # Custom Device Settings
        CAMERA_DEVICE_SETTINGS = "CameraDeviceSettings"
        CAMERA_DEVICE_SETTINGS_SUCCESS = "CameraDeviceSettingsSuccess"
        
        # Single Image Analysis INformation
        SI_FILEPATH_CALIB = "SIFilepathCalib"
        SI_FILEPATH_TARGET = "SIFilepathTarget"
        SI_RESULT = "SiResult"
        
        PELLET_SIZER_IMAGES = "PelletSizerImages"
        PELLET_SIZER_RESULT = "PelletSizerResult"
        
    class Namespaces(Enum):
        CONTROLLER = "Controller"
        DEVICES = "Devices"
        MEASUREMENT = "Measurement"
        MIXING_TIME = "MixingTime"
        PROJECT_MANAGEMENT = "ProjectManagement"
        DEFAULT = "default"
        
        LIVE_DATA = 'LiveData'
        
        ARDUINO = "Arduino"
        CAMERA = "Camera"
        PUMP = "Pump"
        MFC = "MFC"

    class Tags(Enum):
        pass
        
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(InMemoryData, cls).__new__(cls)
                cls._instance.namespaces = {"default": {"data": {}, "key_to_uid": {}, "uid_ref_count": {}}}
                cls._instance.tags = {}
            return cls._instance

    def _generate_uid(self):
        uid = str(uuid.uuid4())
        return uid

    def _values_equal(self, val1, val2):
        """
        A robust comparison function that uses iterative strategy to avoid maximum recursion depth issues.
        """
        
        def is_equal(val1, val2, checked_pairs):
            if (id(val1), id(val2)) in checked_pairs:  # Circular reference check
                return True
            checked_pairs.add((id(val1), id(val2)))

            if isinstance(val1, np.ndarray) and isinstance(val2, np.ndarray):
                return np.array_equal(val1, val2)
            if isinstance(val1, dict) and isinstance(val2, dict):
                if len(val1) != len(val2):
                    return False
                for k in val1:
                    if k not in val2 or not is_equal(val1[k], val2[k], checked_pairs):
                        return False
                return True
            if isinstance(val1, list) and isinstance(val2, list):
                if len(val1) != len(val2):
                    return False
                for item1, item2 in zip(val1, val2):
                    if not is_equal(item1, item2, checked_pairs):
                        return False
                return True
            if isinstance(val1, set) and isinstance(val2, set):
                return val1 == val2  # Sets can be compared directly
            # Add more types if necessary...
            return val1 == val2

        try:
            return is_equal(val1, val2, set())
        except RecursionError:
            print("RecursionError: Data too deeply nested or circular reference detected.")
            return False  # or handle appropriately

    def _get_namespace(self, namespace):
        if namespace not in self.namespaces:
            # Automatically create the namespace if it does not exist
            self.namespaces[namespace] = {"data": {}, "key_to_uid": {}, "uid_ref_count": {}}
        return self.namespaces[namespace]

    def create_namespace(self, namespace):
        with self._lock:
            if namespace in self.namespaces:
                raise ValueError(f"Namespace '{namespace}' already exists.")
            self.namespaces[namespace] = {"data": {}, "key_to_uid": {}, "uid_ref_count": {}}

    def delete_namespace(self, namespace):
        with self._lock:
            if namespace == "default":
                raise ValueError("Cannot delete the default namespace.")
            if namespace in self.namespaces:
                del self.namespaces[namespace]
            else:
                raise ValueError(f"Namespace '{namespace}' does not exist.")

    def add_data(self, keys, value, namespace="default", tags=None):
        if not isinstance(keys, (list, tuple)):
            keys = [keys]
        
        if tags is None:
            tags = []
        if not isinstance(tags, list):
            tags = [tags]
        
        with self._lock:
            ns = self._get_namespace(namespace)
            existing_data_uid = None
            existing_uids_checked = set()
            for key in keys:
                uid = ns["key_to_uid"].get(key)
                if uid and uid not in existing_uids_checked:
                    if self._values_equal(ns["data"].get(uid), value):
                        existing_data_uid = uid
                        break
                    existing_uids_checked.add(uid)
            
            if existing_data_uid is None:
                existing_data_uid = self._generate_uid()
                ns["data"][existing_data_uid] = value

            for tag in tags:
                if tag not in self.tags:
                    self.tags[tag] = set()
                self.tags[tag].add((existing_data_uid, namespace))
            
            for key in keys:
                old_uid = ns["key_to_uid"].get(key)
                if old_uid:
                    ns["uid_ref_count"][old_uid] -= 1
                    if ns["uid_ref_count"][old_uid] == 0 and old_uid not in ns["key_to_uid"].values():
                        del ns["data"][old_uid]
                        del ns["uid_ref_count"][old_uid]
                ns["key_to_uid"][key] = existing_data_uid
                ns["uid_ref_count"][existing_data_uid] = ns["uid_ref_count"].get(existing_data_uid, 0) + 1

    def get_data(self, key, namespace="default", uid=None):
        """Uid and key are exclusive!"""
        with self._lock:
            ns = self._get_namespace(namespace)
            if uid is None:
                uid = ns["key_to_uid"].get(key)
            else:
                uid = uid
            if uid and uid in ns["data"]:
                value = ns["data"][uid]
                if isinstance(value, (dict, list, set, np.ndarray)):
                    return copy.deepcopy(value)
                return ns["data"][uid]
            return None

    def delete_data(self, keys, namespace="default"):
        if not isinstance(keys, (list, tuple)):
            keys = [keys]
        
        with self._lock:
            ns = self._get_namespace(namespace)
            for key in keys:
                uid = ns["key_to_uid"].pop(key, None)
                if uid:
                    ns["uid_ref_count"][uid] -= 1
                    if ns["uid_ref_count"][uid] == 0:
                        del ns["data"][uid]
                        del ns["uid_ref_count"][uid]

    def remove_tags(self, uid, namespace, tags):
        with self._lock:
            for tag in tags:
                if tag in self.tags and (uid, namespace) in self.tags[tag]:
                    self.tags[tag].remove((uid, namespace))
                    if not self.tags[tag]:
                        del self.tags[tag]

    def get_data_by_tag(self, tag):
        with self._lock:
            if tag in self.tags:
                uid_namespace_pairs = self.tags[tag]
                return {uid: self.get_data(uid=uid, namespace=namespace) for uid, namespace in uid_namespace_pairs}
            return {}

    def _remove_uid_from_tags(self, uid, namespace):
        uid_namespace_pair = (uid, namespace)
        for tag in list(self.tags.keys()):
            if uid_namespace_pair in self.tags[tag]:
                self.tags[tag].remove(uid_namespace_pair)
                if not self.tags[tag]:
                    del self.tags[tag]

    def purge_all_data(self, namespace="default"):
        with self._lock:
            ns = self._get_namespace(namespace)
            ns["data"].clear()
            ns["key_to_uid"].clear()
            ns["uid_ref_count"].clear()

    def check_key(self, key, namespace="default"):
        ns = self._get_namespace(namespace)
        return key in ns["key_to_uid"]

    def list_namespaces(self):
        with self._lock:
            return list(self.namespaces.keys())

    ### THIS IS A TEST ###
    
    def generate_enums_file(self, file_name='generated_enums.py'):
        """
        Generates a Python file with Enum classes for Keys, Namespaces, and Tags.
        The file is created in the current directory with the specified name.
        
        Args:
            file_name (str): The name of the file to generate (default is 'generated_enums.py').
        """
        # Collect Keys, Namespaces, and Tags
        keys = set()  # to store all unique keys across namespaces
        namespaces = set(self.namespaces.keys())  # namespaces
        tags = set(self.tags.keys())  # tags
        
        # Iterate over all namespaces and collect keys
        for namespace_data in self.namespaces.values():
            keys.update(namespace_data["key_to_uid"].keys())
        
        # Create the content of the enums
        enum_content = []

        # Write Enums for Keys
        enum_content.append("from enum import Enum\n\n\n")
        enum_content.append("class Keys(Enum):\n")
        for key in sorted(keys):
            enum_content.append(f"    {key.upper()} = \"{key}\"\n")
        if not keys:
            enum_content.append("    pass\n")  # In case there are no keys

        enum_content.append("\n\n")

        # Write Enums for Namespaces
        enum_content.append("class Namespaces(Enum):\n")
        for namespace in sorted(namespaces):
            enum_content.append(f"    {namespace.upper()} = \"{namespace}\"\n")
        if not namespaces:
            enum_content.append("    pass\n")  # In case there are no namespaces

        enum_content.append("\n\n")

        # Write Enums for Tags
        enum_content.append("class Tags(Enum):\n")
        for tag in sorted(tags):
            enum_content.append(f"    {tag.upper()} = \"{tag}\"\n")
        if not tags:
            enum_content.append("    pass\n")  # In case there are no tags

        # Generate the file
        with open(file_name, 'w') as f:
            f.writelines(enum_content)

        print(f"Enum file '{file_name}' generated successfully.")
