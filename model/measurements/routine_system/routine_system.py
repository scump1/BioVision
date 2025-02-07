from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Dict
from uuid import uuid4
from threading import Lock

from operator_mod.logger.global_logger import Logger

class RoutineData:

    class Parameter(Enum):
        MFC = "M"
        PUMP = "P"
        CAMERA = "C"
        ALGORITHMS = "A"
        LIGHTMODE = "L"
        
        # Parameters for checking conditions
        TEMPERATURE = "T"
        RESULT_NUMBER = "R"

    class ConditionType(Enum):
        GREATER_THAN = ">"
        LESS_THAN = "<"
        EQUAL_TO = "=="

    class LightMode(Enum):
        ALWAYS_ON = 1
        ON_WHEN_NEEDED = 2
        ALWAYS_OFF = 0

    class InteractionType(Enum):
        STOP_AND_WAIT = 0
        
    class AlgorithmType(Enum):
        BUBBLE_SIZE = 0
        PELLET_SIZE = 1

    @dataclass
    class MaFlCo:
        massflow: float
        interrupt: bool = False

    @dataclass
    class Pump:
        volume: float
        interval: float = None

    @dataclass
    class Camera:
        img_count: int
        interval: float

    @dataclass
    class Temperature:
        target: float
        
    @dataclass
    class Light:
        mode: 'RoutineData.LightMode'

    @dataclass
    class Algorithm:
        algorithm: 'RoutineData.AlgorithmType'

    @dataclass
    class ParameterCondition:
        parameter: 'RoutineData.Parameter'
        condition_type: 'RoutineData.ConditionType'
        target_value: float

        def evaluate(self, current_value: float) -> bool:
            if self.condition_type == RoutineData.ConditionType.GREATER_THAN:
                return current_value > self.target_value
            elif self.condition_type == RoutineData.ConditionType.LESS_THAN:
                return current_value < self.target_value
            elif self.condition_type == RoutineData.ConditionType.EQUAL_TO:
                return current_value == self.target_value
            else:
                raise ValueError(f"Unsupported condition type: {self.condition_type}")

    @dataclass
    class Subroutine:
        interval: float
        duration: float
        setting: Any

    @dataclass
    class Setting:
        name: 'RoutineData.Parameter'
        setting: Any  # Use Any to allow any type of setting
        subroutines: List['RoutineData.Subroutine'] = field(default_factory=list)

    @dataclass
    class Slot:
        name: str
        runtime: float
        settings: List['RoutineData.Setting'] = field(default_factory=list)
        condition: 'RoutineData.ParameterCondition' = None
        interaction: 'RoutineData.InteractionType' = None
        uid: str = field(default_factory=lambda: str(uuid4()))

class RoutineSystem:
    
    _instances = {}
    _lock = Lock()
    
    def __new__(cls, name: str):
        with cls._lock:
            if name not in cls._instances:
                instance = super(RoutineSystem, cls).__new__(cls)
                cls._instances[name] = instance
        return cls._instances[name]
    
    def __init__(self, name: str):
        self.name = name
        self.slots: List[RoutineData.Slot] = []
        
        self.logger = Logger("Application").logger

    def create_slot(self, name: str, runtime: float) -> RoutineData.Slot:
        slot = RoutineData.Slot(name=name, runtime=runtime)
        self.slots.append(slot)
        return slot

    def add_setting_to_slot(self, slot_uid: str, setting: RoutineData.Setting):
        slot = self._find_slot_by_uid(slot_uid)
        if slot:
            slot.settings.append(setting)

    def add_subroutine_to_setting(self, slot_uid: str, setting_name: RoutineData.Parameter, subroutine: RoutineData.Subroutine):
        slot = self._find_slot_by_uid(slot_uid)
        if slot:
            setting = self._find_setting_in_slot(slot, setting_name)
            if setting:
                setting.subroutines.append(subroutine)

    def delete_slot(self, slot_uid: str):
        self.slots = [slot for slot in self.slots if slot.uid != slot_uid]

    def delete_setting_from_slot(self, slot_uid: str, setting_name: RoutineData.Parameter):
        slot = self._find_slot_by_uid(slot_uid)
        if slot:
            slot.settings = [setting for setting in slot.settings if setting.name != setting_name]

    def delete_subroutine_from_setting(self, slot_uid: str, setting_name: RoutineData.Parameter, subroutine: RoutineData.Subroutine):
        slot = self._find_slot_by_uid(slot_uid)
        if slot:
            setting = self._find_setting_in_slot(slot, setting_name)
            if setting:
                setting.subroutines = [sr for sr in setting.subroutines if sr != subroutine]

    def evaluate_conditions(self, current_values: Dict[RoutineData.Parameter, float]) -> List[str]:
        satisfied_slots = []
        for slot in self.slots:
            current_value = current_values.get(slot.condition.parameter)
            if current_value is not None and slot.condition.evaluate(current_value):
                satisfied_slots.append(slot.name)
        return satisfied_slots

    def _find_slot_by_uid(self, slot_uid: str) -> RoutineData.Slot:
        for slot in self.slots:
            if slot.uid == slot_uid:
                return slot
        raise self.logger.warning(f"Slot with UID {slot_uid} not found")

    def _find_setting_in_slot(self, slot: RoutineData.Slot, setting_name: RoutineData.Parameter) -> RoutineData.Setting:
        for setting in slot.settings:
            if setting.name == setting_name:
                return setting
        raise self.logger.warning(f"Setting with name {setting_name} not found in slot {slot.name}")

    def create_parameter_setting(self, param: RoutineData.Parameter, **kwargs) -> Any:
        mapping = {
            RoutineData.Parameter.MFC: RoutineData.MaFlCo,
            RoutineData.Parameter.PUMP: RoutineData.Pump,
            RoutineData.Parameter.CAMERA: RoutineData.Camera,
            RoutineData.Parameter.TEMPERATURE: RoutineData.Temperature,
        }
        param_class = mapping.get(param)
        if param_class:
            return param_class(**kwargs)
        raise self.logger.error(f"Invalid parameter type: {param}")
    
    @classmethod
    def get_instance(cls, name: str):
        return cls._instances.get(name, None)