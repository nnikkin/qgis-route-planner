from qgis.PyQt.QtCore import pyqtSignal, QObject

from enum import Enum


class FormMode(Enum):
    EMPTY = 0
    VIEW = 1
    EDIT = 2


class SettingsModel(QObject):
    active_profile_id_changed = pyqtSignal(object)
    current_profile_id_changed = pyqtSignal(object)
    profile_editing_state_changed = pyqtSignal(bool)
    profiles_changed = pyqtSignal(list)

    def __init__(self):
        super().__init__()

        self.__active_profile_id: int = None
        self.__current_profile_id: int = None

        self.__editing_mode: FormMode = FormMode.EMPTY
        self.__is_editing_enabled: bool = self.__editing_mode == FormMode.EDIT

        self.__profiles: list = []

    @property
    def active_profile_id(self) -> int:
        return self.__active_profile_id

    @property
    def current_profile_id(self) -> int:
        return self.__current_profile_id

    @property
    def is_editing_enabled(self) -> bool:
        return self.__is_editing_enabled

    @property
    def editing_mode(self) -> FormMode:
        return self.__editing_mode

    @property
    def profiles(self) -> list:
        return self.__profiles

    @editing_mode.setter
    def editing_mode(self, value: FormMode):
        self.__editing_mode = value
        self.__is_editing_enabled = self.__editing_mode == FormMode.EDIT
        self.profile_editing_state_changed.emit(self.__is_editing_enabled)

    @current_profile_id.setter
    def current_profile_id(self, value: int):
        self.__current_profile_id = value
        self.current_profile_id_changed.emit(value)

    @active_profile_id.setter
    def active_profile_id(self, value: int):
        self.__active_profile_id = value
        self.active_profile_id_changed.emit(value)

    @profiles.setter
    def profiles(self, profiles: list):
        self.__profiles = profiles
        self.profiles_changed.emit(profiles)
