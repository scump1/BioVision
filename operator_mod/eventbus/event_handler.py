from enum import Enum
import threading

from concurrent.futures import ThreadPoolExecutor
from typing import Callable
from PySide6.QtCore import QThread, Signal

from operator_mod.logger.global_logger import Logger

class GUIWorker(QThread):
        # Signal to process events on the GUI thread
        gui_signal = Signal()

        def __init__(self, event_logger, event_name, *args, **kwargs):

            super().__init__()
            
            self.event_logger = event_logger
            self.gui_signal.connect(lambda: self._process_event(event_name, *args, **kwargs))

        def _process_event(self, event_name, *args, **kwargs):
            try:
                listeners_to_notify = EventManager.get_instance().get_listeners(event_name)

                for listener, _, _ in listeners_to_notify:
                    listener(*args, **kwargs)
                    self.event_logger.info(f"Triggered GUI Event: {event_name} with arguments {args} and {kwargs}.")
            except Exception as e:
                self.event_logger.error(f"Could not trigger event: {e}.")

class EventManager():
    """Global Event Manager that handles ALL Events. Based on listener interaction. Thread safe and singleton.
    Args:
        metaclass (NEVER CHANGE): Ensures the Singleton Instance is applied properly. Defaults to SingletonMeta.
    """
    
    _instance = None
    _lock = threading.Lock()

    class EventKeys(Enum):
            
        # Generals
        APPLICATION_SHUTDOWN = "ApplicationShutdown"
        STATUS_BAR_UPDATE = "StatusBarUpdate"
        PROFILE_SETTER = "ProfileSetter"
        
        DELETE_SLOT_LIST = "DeleteSlotList"
        NEW_SLOT_LIST = "NewSlotList"
        CURRENT_SLOT_CHANGED = "CurrentSlotChanged"
        UPDATE_TO_TOPMOST_SLOT = "UpdateToTopmostSlot"
        
        ####
        
        LIVE_VIEW_STATE_ENTERED = "LiveViewStateEntered"
        LIVE_VIEW_STATE_TERMINATED = "LiveViewStateTerminated"

        # GUIS
        GUI_NEW_PROJECT = "GUINewProject"
        GUI_OPEN_PROJECT = "OpenProject"
        GUI_CLOSE_PROJECT = "CloseProject"
        GUI_SAVE_PRETEND = "SavePretend"
        GUI_SAVE_PROJECT = "SaveProject"
        
        SI_FORM_BACK_BUTTON = "SIFormBackButton"
        
        # Routine
        MS_PROGRESS_SLOT = "CurrentMeasurementProgressLog"
        MS_STOPPED_FOR_WAITING = "MEasurementStoppedForWaiting"
        MS_ENDED = "MSEnded"
        
        # Config Setter
        CONFIGURATION_SETTER_PUMP = "ConfigurationSetterPump"
        CONFIGURATION_SETTER_MFC = "ConfigurationSetterMFC"
        
    def __new__(cls, *args, **kwargs):
        
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EventManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        
        # Idempotent init
        if hasattr(self, 'initialized') and self.initialized:
            return
        
        self.initialized = True
    
        self.listeners = {}
        
        self.event_logger = Logger("EventManager").logger
        
        # Initialize thread pool executor for non-GUI events
        self.executor = ThreadPoolExecutor(max_workers=10)

    def __del__(self):
        self._shutdown()
        
    def _shutdown(self):
        """Gracefully shutdown the Event Manager."""
        try:
            if self.executor:
                self.executor.shutdown(wait=False, cancel_futures=True)

        except Exception as e:
            self.event_logger.critical(f"Shutdown Error: {e}.")
    
    def _execute_listener(self, listener: Callable, *args, **kwargs):
        """Helper method to execute a listener and log the event."""
        listener(*args, **kwargs)
        
    def get_listeners(self, event_name):
        """Get all listeners for a given event."""
        with self._lock:
            return list(self.listeners.get(event_name, []))
    
    def register_event(self, event_name: str | EventKeys):
        
        self.event_logger.info("Added Event")
        with self._lock:
            if event_name not in self.listeners:
                self.listeners[event_name] = []

    def add_listener(self, event_name: str | EventKeys, listener: Callable, priority: int = 0, gui_safe: bool = False) -> None:
        """Add a listener to an event. Set gui_safe=True for listeners requiring GUI thread."""

        if event_name not in self.listeners:
            self.listeners[event_name] = []
            
        self.listeners[event_name].append((listener, priority, gui_safe))
        self.listeners[event_name].sort(key=lambda x: x[1], reverse=True)
        
        self.event_logger.info(f"Added event {event_name} with listener {listener}.")

    def remove_listener(self, event_name: str | EventKeys, listener: Callable) -> None:
        """Remove a listener from an event."""
        with self._lock:
            if event_name in self.listeners:
                self.listeners[event_name] = [l for l in self.listeners[event_name] if l[0] != listener]

    def trigger_event(self, event_name: str | EventKeys, *args, **kwargs) -> None:
        """Trigger an event. If gui_safe, dispatch via GUI thread; else use ThreadPoolExecutor."""
        
        with self._lock:
            listeners_to_notify = list(self.listeners.get(event_name, []))
        
        for listener, _, gui_safe in listeners_to_notify:
            if gui_safe:
                # Send to GUI thread using Signal/Slot mechanism
                gui_worker = GUIWorker(self.event_logger, event_name, *args, **kwargs)
                gui_worker.gui_signal.emit()
                
            else:
                # Dispatch non-GUI tasks to the ThreadPoolExecutor
                self.executor.submit(self._execute_listener, listener, *args, **kwargs)
            
                self.event_logger.info(f"Triggered event {event_name} with listener(s) {listeners_to_notify}.")
            
    @classmethod
    def get_instance(self):
        return self._instance