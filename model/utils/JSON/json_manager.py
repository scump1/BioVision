import os
import json
import threading

from model.utils.file_access.file_access_manager import FileAccessManager
from operator_mod.logger.global_logger import Logger

class JSONManager:
    
    _lock = threading.Lock()
    
    def __init__(self) -> None:
        
        self.fam = FileAccessManager()
        
        self.logger = Logger("Model").logger
    
    def write_json(self, data: dict, target_dir_path: str, filename: str, overwrite : bool = False) -> None:
        """
        Writes a given data dictionary to a JSON file in the target directory.
        
        Args:
            data (dict): The dictionary to write to the file.
            target_dir (str): The directory path where the file should be saved.
            filename (str): The name of the file to save.
        """
        file_path = os.path.join(target_dir_path, f"{filename}.json")
        
        # Ensure the directory exists
        os.makedirs(target_dir_path, exist_ok=True)
    
        if not overwrite:
            if os.path.exists(file_path):
                self.add_to_json(data, file_path)
                return
        
        # Write the JSON data to the file
        try:
            with self._lock:
                self.fam.get_access(file_path)
                with open(file_path, 'w') as file:
                    json.dump([data], file, indent=4)
                self.logger.info(f"Successfully wrote to {file_path}")
        except Exception as e:
            self.logger.error(f"Error writing to {file_path}: {e}")
        finally:
            self.fam.release_access(file_path)
            
    def load_json(self, path: str) -> dict:
        """Loads available data from a given path."""
        if not os.path.exists(path):
            self.logger.warning(f"The path {path} does not exist.")
            return None
        
        try:
            with self._lock:
                self.fam.get_access(path)
                with open(path, 'r') as file:
                    data = json.load(file)
                self.logger.info(f"Successfully loaded data from {path}.")
                return data
            
        except Exception as e:
            self.logger.error(f"Error loading from file {path}: {e}")
            return None
        
        finally:
            self.fam.release_access(path)
    
    def add_to_json(self, data: dict, file_path: str) -> None:
        """Adds data to an existing json file gracefully."""
        
        if not os.path.exists(file_path):
            self.logger.warning(f"The file {file_path} does not exist.")
            return
        
        try:
            with self._lock:
                self.fam.get_access(file_path)
                
                # Open the file and load the existing data
                with open(file_path, 'r+') as file:
                    file_data = json.load(file)
                    
                    # Check if the current content is a list or a dictionary
                    if isinstance(file_data, dict):
                        file_data = [file_data]
                    
                    # If the current content is a list, append the new dictionary
                    if isinstance(file_data, list):
                        file_data.append(data)
                    
                    # Move the file pointer to the beginning of the file
                    file.seek(0)
                    # Overwrite file with updated list
                    json.dump(file_data, file, indent=4)
                    file.truncate()
                    
                self.logger.info(f"Successfully updated {file_path}")
        except Exception as e:
            self.logger.error(f"Error updating {file_path}: {e}")
        finally:
            self.fam.release_access(file_path)
            
    def delete_from_json(self, target_key: str, path: str) -> None:
        """Tries to delete the specified target_key from a JSON file gracefully."""
        
        if not os.path.exists(path):
            self.logger.warning(f"The file {path} does not exist.")
            return
        
        try:
            with self._lock:
                self.fam.get_access(path)
                
                # Open the file and load the existing data
                with open(path, 'r+') as file:
                    data = json.load(file)
                    
                    if isinstance(data, dict) and target_key in data:
                        # Delete key from dictionary
                        del data[target_key]
                    elif isinstance(data, list):
                        # Delete key from dictionaries in a list
                        for item in data:
                            if isinstance(item, dict) and target_key in item:
                                del item[target_key]
                    
                    # Move the file pointer to the beginning of the file
                    file.seek(0)
                    # Overwrite file with updated data
                    json.dump(data, file, indent=4)
                    file.truncate()
                        
                self.logger.info(f"Successfully deleted key {target_key} from {path}")
        except Exception as e:
            self.logger.error(f"Error deleting key {target_key} from {path}: {e}")
        finally:
            self.fam.release_access(path)
