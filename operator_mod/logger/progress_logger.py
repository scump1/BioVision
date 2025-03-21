from threading import Lock
import datetime

class ProgressLogger:
    """Logs progress for a task across different score spaces within that task. 
    Each score space has an associated target score, and progress can be tracked independently for each space.
    Multiple logger instances can be managed, secured by an instance-level lock.

    Attributes:
        spaces (dict): A dictionary mapping score space names to their target scores.
        space_logger (dict): A dictionary mapping score space names to their current progress.
        metadata (dict): A dictionary containing metadata about the creation and completion times of score spaces.
    """

    _instances = {}
    _lock = Lock()

    def __new__(cls, name: str):
        with cls._lock:
            if name not in cls._instances:
                instance = super().__new__(cls)
                instance.spaces = {}
                instance.space_logger = {}
                instance.metadata = {}
                cls._instances[name] = instance
        return cls._instances[name]

    def add_scorespace(self, name: str, targetscore: int):
        """Adds a score space to the logger. A score space is a segment of a task with an associated target score.

        Args:
            name (str): The name of the score space.
            targetscore (int): The target score for the space (must be > 0).

        Raises:
            ValueError: If targetscore is not a positive integer.
        """
        if not name:
            return
        if targetscore <= 0:
            return
        
        if name not in self.spaces:
            self.spaces[name] = targetscore
            self.space_logger[name] = 0
            self.metadata[name] = [datetime.datetime.now().strftime("%H:%M:%S")]

    def update_scorespace_target(self, name: str, targetscore: int):
        """Updates the target score for a given score space.

        Args:
            name (str): The name of the score space.
            targetscore (int): The new target score (must be > 0).

        Raises:
            ValueError: If targetscore is not a positive integer.
            KeyError: If the score space name does not exist.
        """
        if targetscore <= 0:
            return
        if name not in self.spaces:
            return

        self.spaces[name] = targetscore

    def del_scorespace(self, name: str, purge=False):
        """Deletes a score space from the logger.

        Args:
            name (str): The name of the score space.
            purge (bool): If true deletes all data in the Logger used

        Raises:
            KeyError: If the score space name does not exist.
        """
        
        if purge is True:
            self.spaces.clear()
            self.space_logger.clear()
            self.metadata.clear()
        
        elif name in self.spaces:
            del self.spaces[name]
            del self.space_logger[name]
            del self.metadata[name]
        else:
            return

    def progress_space(self, name: str, increment: int):
        """Increments the progress of a score space.

        Args:
            name (str): The name of the score space.
            increment (int): The amount by which to increment the score.

        Raises:
            ValueError: If increment is not a positive integer.
            KeyError: If the score space name does not exist.
        """
        if increment < 0:
            return
        if name not in self.space_logger:
            return

        self.space_logger[name] = min(self.space_logger[name] + increment, self.spaces[name])

        if self._completed_space(name):
            self._track_metadata(name)

    def set_space_value(self, name:str, value:int):
        """Sets a value to a specified space in the task progress. Not recommended for use.

        Args:
            name (str): The name of the score space.
            value (int): Any value > 0.

        Raises:
            ValueError: If the value is not a positive integer.
            KeyError: If the score space name does not exist.
        """
        if value < 0:
            return
        if name not in self.space_logger:
            return

        if value > self.spaces[name]:
            self.space_logger[name] = self.spaces[name]
        else:
            self.space_logger[name] = value

    def _completed_space(self, name: str) -> bool:
        """Checks if a score space has reached its target score.

        Args:
            name (str): The name of the score space.

        Returns:
            bool: True if the score space is complete, otherwise False.
        """
        return self.space_logger[name] >= self.spaces[name]

    def get_progress(self, name = None) -> list:
        """Retrieves progress information.

        Args:
            name (str, optional): The name of the score space to get progress for. Defaults to None.

        Returns:
            list: A list containing [name, target, current] for a specific space or [progress_total] as a percentage.
        """

        if name is None:
            progress_target_sum = sum(self.spaces.values())
            sum_of_progress = sum(self.space_logger.values())

            if progress_target_sum == 0:
                return [0.0]

            progress_percentage = (sum_of_progress / progress_target_sum) * 100
            return [progress_percentage]
        
        elif name is not None:
            if name in self.spaces:
                return [name, self.spaces[name], self.space_logger[name]]
            else:
                return
        
    def get_metadata(self, name = None) -> list | dict:
        """Retrieves metadata for a score space or all score spaces.

        Args:
            name (str, optional): The name of the score space to get metadata for. Defaults to None.

        Returns:
            list | dict: Metadata for a specific space or all spaces.
        """
        if name is not None:
            if name in self.metadata:
                return self.metadata[name]
            else:
                return
        
        return self.metadata

    def _track_metadata(self, name: str):
        """Tracks the completion time of a score space.

        Args:
            name (str): The name of the score space.
        """
        if name in self.metadata:
            self.metadata[name].append(datetime.datetime.now().strftime("%H:%M:%S"))