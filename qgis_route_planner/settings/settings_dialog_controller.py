from __future__ import annotations
from typing import TYPE_CHECKING

from qgis_route_planner.settings.profile_provider import ProfileProvider
from qgis_route_planner.settings.weather_provider import WeatherSettingsProvider

if TYPE_CHECKING:
    from .settings_model import SettingsModel
    from .settings_service import SettingsService
    from qgis_route_planner.vehicle.vehicle_type import VehicleType

from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot, QObject

from qgis_route_planner.presentation import FormMode


class SettingsDialogController(QObject):
    """ Контроллер окна настроек """

    open_page_requested = pyqtSignal(int)
    request_delete_confirmation = pyqtSignal(str, bool)

    reconnect_requested = pyqtSignal()
    graph_rebuild_requested = pyqtSignal()
    weather_settings_saved = pyqtSignal(dict)

    select_distance_setting_saved = pyqtSignal(float)

    active_profile_changed = pyqtSignal(object)

    show_error = pyqtSignal(str)
    show_warning = pyqtSignal(str)
    show_info = pyqtSignal(str)

    def __init__(
            self,
            model: SettingsModel,
            settings_service: SettingsService,
            profile_provider: ProfileProvider,
            weather_provider: WeatherSettingsProvider
    ):
        super().__init__()

        self.__model = model
        self.__service = settings_service
        self.__profile_provider = profile_provider
        self.__weather_provider = weather_provider

    def open_dialog_tab(self, tab_index: int = 0):
        """ Открыть диалог настроек """
        self.__load_initial_state()
        self.open_page_requested.emit(tab_index)

    def get_select_point_distance(self):
        return self.__model.point_select_distance

    def __load_initial_state(self):
        """ Загрузить начальное состояние """
        self.__load_db_params()
        self.__load_profiles()
        self.__load_graph_settings()
        self.__load_weather_settings()
        self.__model.current_profile_id = None
        self.__model.current_profile_data = None
        self.__model.editing_mode = FormMode.EMPTY

    def __load_db_params(self):
        """ Загрузить параметры БД в модель """
        try:
            db = self.__service.load_db_params()
            self.__model.db_params = db
        except Exception as e:
            self.show_error.emit(f"Ошибка загрузки параметров подключения к БД: {e}")

    def __load_profiles(self):
        """ Загрузить список профилей в модель """
        try:
            self.__model.profiles = self.__profile_provider.get_profiles()
            self.__model.active_profile_id = self.__service.get_active_profile_id()
        except Exception as e:
            self.show_error.emit(f"Ошибка загрузки профилей ТС: {e}")

    def __load_graph_settings(self):
        try:
            self.__model.point_select_distance = self.__service.load_select_distance_setting()
        except Exception as e:
            self.show_error.emit(e)

    def __load_weather_settings(self):
        """ Загрузить настройки погодного сервиса в модель """
        try:
            self.__model.weather_settings = self.__service.load_weather_settings()
        except Exception as e:
            self.show_error.emit(f"Ошибка загрузки настроек погодного сервиса: {e}")

    @pyqtSlot()
    def change_db_connection(self):
        """ Запрос на изменение параметров БД """
        self.reconnect_requested.emit()

    @pyqtSlot()
    def rebuild_graph(self):
        """ Запросить перестроение графа """
        self.graph_rebuild_requested.emit()

    @pyqtSlot(float)
    def save_graph_settings(self, dist_value: float):
        try:
            self.__service.save_graph_settings(dist_value)
            self.__load_graph_settings()
            self.select_distance_setting_saved.emit(self.__model.point_select_distance)
            self.show_info.emit("Настройки сохранены")
        except Exception as e:
            self.show_error.emit(f"Ошибка сохранения настроек графа: {e}")

    @pyqtSlot(str, str, str, float, float)
    def save_weather_settings(
            self,
            api_key: str,
            fallback_season: str,
            summer_avg_speed_kmh: float,
            winter_avg_speed_kmh: float,
    ):
        """ Сохранить настройки погодного сервиса и сезонных скоростей """
        if summer_avg_speed_kmh <= 0 or winter_avg_speed_kmh <= 0:
            self.show_warning.emit("Средняя скорость должна быть больше 0 км/ч.")
            return

        try:
            self.__service.save_weather_settings(
                api_key.strip(),
                fallback_season,
                summer_avg_speed_kmh,
                winter_avg_speed_kmh,
            )
            self.__load_weather_settings()
            self.weather_settings_saved.emit(self.__model.weather_settings)
            self.show_info.emit("Настройки погодного сервиса сохранены")
        except Exception as e:
            self.show_error.emit(f"Ошибка сохранения настроек погодного сервиса: {e}")

    @pyqtSlot(str, str)
    def check_weather_connection(self, api_url: str, api_key: str):
        """ Проверить подключение к OpenWeatherMap """
        if not api_key.strip():
            self.show_warning.emit("Введите API-ключ OpenWeatherMap.")
            return

        if self.__weather_provider.test_connection():
            self.show_info.emit("Подключение к OpenWeatherMap успешно проверено")
        else:
            self.show_error.emit("Не удалось подключиться к OpenWeatherMap. Проверьте правильность ввода API-ключа.")

    @pyqtSlot()
    def start_profile_create(self):
        """ Начать создание нового профиля """
        self.__model.current_profile_id = None
        self.__model.current_profile_data = None
        self.__model.editing_mode = FormMode.CREATE

    @pyqtSlot()
    def start_profile_edit(self):
        """ Начать редактирование текущего профиля """
        if self.__model.current_profile_id is None:
            return
        self.__model.editing_mode = FormMode.EDIT

    @pyqtSlot()
    def cancel_profile_edit(self):
        """ Отменить редактирование профиля """
        if self.__model.current_profile_id is None:
            self.__model.editing_mode = FormMode.EMPTY
            return

        self.__load_current_profile_data()
        self.__model.editing_mode = FormMode.VIEW

    def __load_current_profile_data(self):
        """ Загрузить данные текущего профиля в модель """
        if self.__model.current_profile_id is None:
            self.__model.current_profile_data = None
            return
        try:
            profile = self.__profile_provider.get_profile_by_id(self.__model.current_profile_id)
            self.__model.current_profile_data = profile
        except Exception as e:
            self.show_error.emit(f"Ошибка загрузки профиля: {e}")
            self.__model.current_profile_data = None

    @pyqtSlot(int)
    def select_profile(self, profile_id: int):
        """ Выбрать профиль для просмотра/редактирования """
        self.__model.current_profile_id = profile_id
        if profile_id is None:
            self.__model.current_profile_data = None
            self.__model.editing_mode = FormMode.EMPTY
            return

        self.__load_current_profile_data()
        self.__model.editing_mode = FormMode.VIEW

    @pyqtSlot(str, object, float, float, float, float)
    def save_profile(self, name: str, vehicle_type: VehicleType, height: float, width: float, depth: float,
                     weight: float):
        """ Сохранить профиль """
        mode = self.__model.editing_mode
        if not (mode == FormMode.EDIT or mode == FormMode.CREATE):
            return

        if not name or not name.strip():
            self.show_warning.emit("Введите название профиля!")
            return

        try:
            profile = self.__profile_provider.create_profile(
                name=name.strip(),
                type=vehicle_type,
                height_m=height,
                width_m=width,
                depth_m=depth,
                weight_t=weight,
            )
            self.__model.current_profile_id = profile.id

            if mode == FormMode.CREATE:
                # Создание нового профиля
                self.show_info.emit("Профиль успешно создан!")
            else:
                # Обновление существующего
                self.__profile_provider.update_profile(self.__model.current_profile_id, profile)
                self.show_info.emit("Профиль успешно обновлен!")

            # Обновить список профилей
            self.__load_profiles()
            self.__load_current_profile_data()
            self.__model.editing_mode = FormMode.VIEW

        except Exception as e:
            self.show_error.emit(f"Ошибка сохранения профиля: {e}")

    @pyqtSlot()
    def request_delete_profile(self):
        """ Запросить подтверждение удаления профиля """
        profile_id = self.__model.current_profile_id
        if profile_id is None:
            return

        try:
            profile = self.__profile_provider.get_profile_by_id(profile_id)
            if profile is None:
                return

            is_active = profile_id == self.__model.active_profile_id
            self.request_delete_confirmation.emit(profile.name, is_active)
        except Exception as e:
            self.show_error.emit(f"Ошибка при запросе удаления профиля: {e}")

    @pyqtSlot()
    def confirm_delete_profile(self):
        """ Подтвержденное удаление профиля """
        try:
            profile_id = self.__model.current_profile_id
            if profile_id is None:
                return

            if len(self.__model.profiles)-1 <= 0:
                self.show_error.emit("Нельзя удалить единственный зарегистрированный профиль")

            is_active = profile_id == self.__model.active_profile_id
            if is_active:
                self.__service.set_active_profile_id(None)
                self.__model.active_profile_id = None

            self.__profile_provider.delete_profile(profile_id)
            self.__model.current_profile_id = None
            self.__model.current_profile_data = None
            self.__model.editing_mode = FormMode.EMPTY

            self.__load_profiles()
            self.show_info.emit("Профиль успешно удалён!")
        except Exception as e:
            self.show_error.emit(f"Ошибка удаления профиля: {e}")

    @pyqtSlot()
    def set_active_profile(self):
        """ Установить текущий профиль как активный """
        profile_id = self.__model.current_profile_id
        if profile_id is None:
            return

        if self.__model.active_profile_id == profile_id:
            return

        try:
            self.__service.set_active_profile_id(profile_id)
            self.__model.active_profile_id = profile_id

            current_profile = self.__model.current_profile_data
            if current_profile:
                self.active_profile_changed.emit(current_profile)

            self.show_info.emit("Активный профиль изменен")
        except Exception as e:
            self.show_error.emit(f"Ошибка установки активного профиля: {e}")
