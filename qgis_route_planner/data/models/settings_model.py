from qgis.PyQt.QtCore import pyqtSignal, QObject
from enum import Enum

from ..vehicle import VehicleProfile


class FormMode(Enum):
    EMPTY = 0
    VIEW = 1
    EDIT = 2


class SettingsModel(QObject):
    """Модель для хранения состояния окна настроек"""

    # Сигналы для БД
    db_params_changed = pyqtSignal(object)

    # Сигналы для профилей
    profiles_changed = pyqtSignal(list)
    active_profile_id_changed = pyqtSignal(object)
    current_profile_id_changed = pyqtSignal(object)
    editing_mode_changed = pyqtSignal(FormMode)
    current_profile_data_changed = pyqtSignal(object)

    def __init__(self):
        super().__init__()

        self.__db_params = None

        self.__profiles: list[VehicleProfile] = []
        self.__active_profile_id: int = None
        self.__current_profile_id: int = None
        self.__editing_mode: FormMode = FormMode.EMPTY
        self.__current_profile_data: VehicleProfile = None

    @property
    def db_params(self):
        return self.__db_params

    @db_params.setter
    def db_params(self, value):
        self.__db_params = value
        self.db_params_changed.emit(value)

    @property
    def profiles(self) -> list[VehicleProfile]:
        return self.__profiles

    @profiles.setter
    def profiles(self, profiles: list[VehicleProfile]):
        self.__profiles = profiles
        self.profiles_changed.emit(profiles)

    @property
    def active_profile_id(self) -> int:
        return self.__active_profile_id

    @active_profile_id.setter
    def active_profile_id(self, value: int):
        self.__active_profile_id = value
        self.active_profile_id_changed.emit(value)

    @property
    def current_profile_id(self) -> int:
        return self.__current_profile_id

    @current_profile_id.setter
    def current_profile_id(self, value: int):
        self.__current_profile_id = value
        self.current_profile_id_changed.emit(value)

    @property
    def editing_mode(self) -> FormMode:
        return self.__editing_mode

    @editing_mode.setter
    def editing_mode(self, value: FormMode):
        self.__editing_mode = value
        self.editing_mode_changed.emit(value)

    @property
    def is_editing_enabled(self) -> bool:
        return self.__editing_mode == FormMode.EDIT

    @property
    def current_profile_data(self) -> VehicleProfile:
        return self.__current_profile_data

    @current_profile_data.setter
    def current_profile_data(self, value: VehicleProfile):
        self.__current_profile_data = value
        self.current_profile_data_changed.emit(value)