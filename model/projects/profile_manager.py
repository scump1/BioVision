
import os
import re
import pickle

from operator_mod.in_mem_storage.in_memory_data import InMemoryData

class ProfileManager:
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ProfileManager, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        
        self.data = InMemoryData()
        
        self.userdata_path = self.data.get_data(self.data.Keys.PROJECT_FOLDER_USERDATA, namespace=self.data.Namespaces.PROJECT_MANAGEMENT)
        
        self._check_folder()

    def _check_folder(self) -> None:
        """Checks for the Profile Subdir in UserData."""
        profilepath = os.path.join(self.userdata_path, "Profiles")
        if not os.path.exists(profilepath):
            os.makedirs(profilepath)
        
        self.profilepath = profilepath
        
    def save_profile(self, name: str, data: object) -> None:
        
        filename = f"{name}.pkl"
        filepath = os.path.join(self.profilepath, filename)
        
        filepath = self.get_next_filename(filepath)

        with open(filepath, "wb") as file:
            pickle.dump(data, file, protocol=pickle.HIGHEST_PROTOCOL)
        
    def list_profiles(self):
        """
        Lists all the available profiles (file names without the `.pkl` extension).
        """
        # List all files in the profile directory
        files = [f for f in os.listdir(self.profilepath) if os.path.isfile(os.path.join(self.profilepath, f))]

        # Filter only .pkl files and return file names without the .pkl extension
        profiles = [os.path.splitext(f)[0] for f in files if f.endswith('.pkl')]
        return profiles
    
    def load_profile(self, name: str):
        """
        Loads a specific profile by its name (without the .pkl extension).
        """
        filename = f"{name}.pkl"
        filepath = os.path.join(self.profilepath, filename)
        
        # Check if the file exists
        if os.path.exists(filepath):
            with open(filepath, "rb") as file:
                return pickle.load(file)
        else:
            return []
        
    def delete_profile(self, name: str) -> None:
        """
        Deletes a profile by its name (without the `.pkl` extension).
        """
        filename = f"{name}.pkl"
        filepath = os.path.join(self.profilepath, filename)
        
        # Check if the file exists and delete it
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Profile '{name}' has been deleted.")
    
    def get_next_filename(self, base_path):
        """
        Finds the next available filename by checking the existing files
        in the directory and determining the highest numbered suffix.
        """
        base_name = os.path.basename(base_path)
        parent_dir = os.path.dirname(base_path)
        name, ext = os.path.splitext(base_name)  # Split name and extension

        # List all files in the parent directory
        existing_files = [f for f in os.listdir(parent_dir) if os.path.isfile(os.path.join(parent_dir, f))]

        # Pattern to match filenames like 'file.txt', 'file (1).txt', 'file (2).txt', etc.
        pattern = re.compile(rf"^{re.escape(name)}(?: \((\d+)\))?{re.escape(ext)}$")

        max_suffix = 0
        for f in existing_files:
            match = pattern.match(f)
            if match:
                suffix = match.group(1)
                if suffix:
                    max_suffix = max(max_suffix, int(suffix))
                else:
                    max_suffix = max(max_suffix, 1)

        next_suffix = max_suffix + 1
        if max_suffix == 0:
            return base_path  # No files with this name, return the original path
        else:
            return os.path.join(parent_dir, f"{name} ({next_suffix}){ext}")
    
    @classmethod
    def get_instance(cls):
        return cls._instance