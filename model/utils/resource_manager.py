import atexit
import json
import copy
from threading import Lock
import datetime

from operator_mod.logger.global_logger import Logger

class ResourceManager:
    """This class manages resource creation and registering for paths, directory creation and structuring, as well as some resource access tasks."""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ResourceManager, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        
        if hasattr(self, '_initialized') and self._initialized:
            return

        # Here we create vital registries
        self.resource_register = {"default": {}, "SaveLocations": {}}
        self.resource_metadata = {"ResourceCount": {}, "ResourceCreation": {}, "ResourceDeletion": {}}
        self.resource_safe = {}

        self.logger = Logger("ResourceManager").logger

        # Register the close method to be called on exit
        atexit.register(self._close)

        self._initialized = True

    def register_resource(self, resourcename, path, space="default"):
        """Register a resource without saving it, just registers the resource with a path."""

        with self._lock:
            if space not in self.resource_register:
                self._create_resource_space(space)

            resourcespace = self.resource_register[space]
            resourcespace[resourcename] = path
            self._update_resource_count(1, space)
            self._update_resource_creation_time(resourcename)

    def get_registered_resources(self, space: str, names=True, paths=False):
        
        with self._lock:
            if space in self.resource_register:
                if names and paths:
                    return copy.deepcopy(self.resource_register.get(space, {}))
                elif names:
                    return copy.deepcopy(list(self.resource_register[space].keys()))
                elif paths:
                    return copy.deepcopy(list(self.resource_register[space].values()))
            else:
                self.logger.warning("Resource Manager - Tried getting resources from unknown space.")
                return None

    def get_resource_spaces(self):
        with self._lock:
            return copy.deepcopy(list(self.resource_register.keys()))

    def deregister_resource(self, resourcename, space="default"):
        with self._lock:
            if space not in self.resource_register:
                self._create_resource_space(space)

            resourcespace = self.resource_register[space]
            resourcespace.pop(resourcename, None)
            self._update_resource_count(-1, space)
            self._update_resource_deletion_time(resourcename)

    def delete_resource_space(self, space="default"):
        """Deletes an entire resource space. Be careful using this."""

        with self._lock:
            if space in self.resource_register:
                for resourcename in list(self.resource_register[space].keys()):
                    self._update_resource_count(-1, space)
                    self._update_resource_deletion_time(resourcename)

                del self.resource_register[space]
            else:
                self.logger.warning(f"Resource space '{space}' does not exist.")

    def save_resource(self, resource, key):
        with self._lock:
            self.resource_safe[key] = resource

    def get_resource(self, key, delete=False):
        with self._lock:
            if key in self.resource_safe:
                resource = copy.deepcopy(self.resource_safe[key])
                if delete:
                    del self.resource_safe[key]
                return resource
            else:
                self.logger.warning("Key does not match any in resource storage.")
                return None

    def delete_resource(self, key):
        with self._lock:
            if key in self.resource_safe:
                del self.resource_safe[key]

    def _create_resource_space(self, spacename):
        if spacename is not None:
            if spacename not in self.resource_register:
                self.resource_register[spacename] = {}

    def _update_resource_count(self, resourcenumber: int, space="default") -> None:
        if space in self.resource_register:
            resourcecountmeta = self.resource_metadata["ResourceCount"]

            if space not in resourcecountmeta:
                resourcecountmeta[space] = 0

            resourcecountmeta[space] += resourcenumber

    def _update_resource_creation_time(self, resourcename):
        if resourcename not in self.resource_metadata["ResourceCreation"]:
            resourcecreation_meta = self.resource_metadata["ResourceCreation"]
            resourcecreation_meta[resourcename] = datetime.datetime.now().strftime("%H:%M:%S")

    def _update_resource_deletion_time(self, resourcename):
        if resourcename not in self.resource_metadata["ResourceDeletion"]:
            resourcedeletion_meta = self.resource_metadata["ResourceDeletion"]
            resourcedeletion_meta[resourcename] = datetime.datetime.now().strftime("%H:%M:%S")

    def _close(self):
        with self._lock:
            self.logger.info("ResourceManager is closing, saving 'SaveLocations' to JSON.")
            dirs_data = self.resource_register.get("SaveLocations")
            try:
                with open(r"model\data\stat\resource_manager\dirs_register.json", "a") as json_file:
                    json.dump(dirs_data, json_file, indent=4)
                self.logger.info("'Dirs' have been successfully saved to .json.")
            except Exception as e:
                self.logger.error(f"Failed to save 'Dirs' to JSON: {e}")

            # Clear the resources regardless of any error in saving
            try:
                self.resource_register.clear()
                self.resource_metadata.clear()
                self.resource_safe.clear()
            except Exception as e:
                self.logger.error(f"Could not cleanup resources: {e}")
            finally:
                self.logger.info("Resource Manager terminated.")
                
    @classmethod
    def get_instance(self):
        return self._instance