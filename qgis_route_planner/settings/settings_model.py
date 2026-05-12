from qgis.PyQt.QtCore import pyqtSignal, QObject

from .profile_dto import ProfileDto
from qgis_route_planner.presentation.form_mode import FormMode


class SettingsModel(QObject):
    """ Модель для хранения состояния окна настроек SettingsDialog """

    # Сигналы для БД
    db_params_changed = pyqtSignal(object)

    # Сигналы для профилей
    profiles_changed = pyqtSignal(list)
    active_profile_id_changed = pyqtSignal(object)
    current_profile_id_changed = pyqtSignal(object)
    editing_mode_changed = pyqtSignal(FormMode)
    current_profile_data_changed = pyqtSignal(object)

    api_credentials_changed = pyqtSignal(str, str)
    api_place_changed = pyqtSignal(float, float)
    weather_settings_changed = pyqtSignal(dict)

    point_select_distance_changed = pyqtSignal(float)

    def __init__(self):
        super().__init__()

        self.__db_params = None

        self.__profiles: list[ProfileDto] = []
        self.__active_profile_id: int = None
        self.__current_profile_id: int = None
        self.__editing_mode: FormMode = FormMode.EMPTY
        self.__current_profile_data: ProfileDto = None
        self.__weather_settings: dict = {}
        self.__point_select_distance: float = 0.1

    @property
    def db_params(self):
        return self.__db_params

    @db_params.setter
    def db_params(self, value):
        self.__db_params = value
        self.db_params_changed.emit(value)

    @property
    def profiles(self) -> list[ProfileDto]:
        return self.__profiles

    @profiles.setter
    def profiles(self, profiles: list[ProfileDto]):
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
    def current_profile_data(self) -> ProfileDto:
        return self.__current_profile_data

    @current_profile_data.setter
    def current_profile_data(self, value: ProfileDto):
        self.__current_profile_data = value
        self.current_profile_data_changed.emit(value)

    @property
    def weather_settings(self) -> dict:
        return self.__weather_settings

    @weather_settings.setter
    def weather_settings(self, value: dict):
        self.__weather_settings = value or {}
        self.weather_settings_changed.emit(self.__weather_settings)

    @property
    def point_select_distance(self):
        return self.__point_select_distance

    @point_select_distance.setter
    def point_select_distance(self, value: float):
        self.__point_select_distance = value
        self.point_select_distance_changed.emit(value)

    def is_last_profile(self) -> bool:
        return len(self.__profiles) > 0

    def is_active_profile(self, profile_id: int) -> bool:
        return self.__active_profile_id == profile_id

