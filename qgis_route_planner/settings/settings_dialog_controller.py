from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .settings_model import SettingsModel
    from .settings_service import SettingsService

from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot, QObject

from qgis_route_planner.presentation import FormMode

from .profile_provider import ProfileProvider
from .weather_provider import WeatherSettingsProvider
from .profile_dto import ProfileDto


class SettingsDialogController(QObject):
    """ Контроллер окна настроек """

    open_page_requested = pyqtSignal(int)
    request_delete_confirmation = pyqtSignal(str)
    reconnect_requested = pyqtSignal()
    graph_rebuild_requested = pyqtSignal()
    weather_settings_saved = pyqtSignal(dict)
    select_distance_setting_saved = pyqtSignal(float)
    basemap_settings_saved = pyqtSignal(dict)
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
        self.__model.selected_profile_id = None
        self.__model.current_profile_data = None
        self.__model.editing_mode = FormMode.EMPTY

    def __load_db_params(self):
        """ Загрузить параметры БД в модель """
        try:
            db = self.__service.load_db_params()
            self.__model.db_params = db
        except Exception as e:
            self.show_error.emit(f"Ошибка загрузки параметров подключения к БД: {e}")

    def __load_profiles(self, select_active: bool = True):
        """ Загрузить список профилей в модель """
        try:
            self.__model.profiles = self.__profile_provider.get_profiles()
            self.__model.active_profile_id = self.__service.get_active_profile_id()
            if select_active:
                self.__model.selected_profile_id = self.__model.active_profile_id
            self.__load_selected_profile_data()
            self.__model.editing_mode = FormMode.VIEW if self.__model.selected_profile_id else FormMode.EMPTY
        except Exception as e:
            self.show_error.emit(f"Ошибка загрузки профилей ТС: {e}")


    def __load_graph_settings(self):
        try:
            settings = self.__service.load_graph_settings()
            self.__model.point_select_distance = float(settings.get("point_select_distance", 10.0))
            self.__model.basemap_settings = {
                "basemap_enabled": bool(settings.get("basemap_enabled", False)),
                "basemap_url": settings.get("basemap_url", ""),
            }
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

    @pyqtSlot(float, bool, str)
    def save_graph_settings(self, dist_value: float, basemap_enabled: bool, basemap_url: str):
        try:
            self.__service.save_graph_settings(dist_value, basemap_enabled, basemap_url)
            self.__load_graph_settings()
            self.select_distance_setting_saved.emit(self.__model.point_select_distance)
            self.basemap_settings_saved.emit(self.__model.basemap_settings)
            self.show_info.emit("Настройки сохранены")
        except Exception as e:
            self.show_error.emit(f"Ошибка сохранения настроек графа: {e}")

    @pyqtSlot(str, str, str)
    def save_weather_settings(
            self,
            api_url: str,
            api_key: str,
            fallback_season: str,
    ):
        """ Сохранить настройки погодного сервиса """
        try:
            self.__service.save_weather_settings(
                api_url.strip(),
                api_key.strip(),
                fallback_season,
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

        try:
            if self.__weather_provider.test_connection(api_url.strip(), api_key.strip()):
                self.show_info.emit("Подключение к OpenWeatherMap успешно проверено")
            else:
                self.show_error.emit("Не удалось подключиться к OpenWeatherMap. Проверьте правильность ввода API-ключа.")
        except Exception as e:
            self.show_error.emit(f"Не удалось подключиться к OpenWeatherMap: {e}")

    @pyqtSlot()
    def start_profile_create(self):
        """ Начать создание нового профиля """
        self.__model.selected_profile_id = None
        self.__model.editing_mode = FormMode.CREATE

    @pyqtSlot()
    def start_profile_edit(self):
        """ Начать редактирование текущего профиля """
        if self.__model.selected_profile_id is None:
            return
        self.__model.editing_mode = FormMode.EDIT

    @pyqtSlot()
    def cancel_profile_edit(self):
        """ Отменить редактирование профиля """
        if self.__model.selected_profile_id is None:
            self.__model.editing_mode = FormMode.EMPTY
            return

        self.__load_selected_profile_data()
        self.__model.editing_mode = FormMode.VIEW

    def __load_selected_profile_data(self):
        """ Загрузить данные текущего профиля в модель """
        if self.__model.selected_profile_id is None:
            self.__model.current_profile_data = None
            return
        try:
            profile = self.__profile_provider.get_profile_by_id(self.__model.selected_profile_id)
            self.__model.current_profile_data = profile
        except Exception as e:
            self.show_error.emit(f"Ошибка загрузки профиля: {e}")
            self.__model.current_profile_data = None

    @pyqtSlot(int)
    def select_profile(self, profile_id: int):
        """ Выбрать профиль для просмотра/редактирования """
        self.__model.selected_profile_id = profile_id

        if profile_id is None:
            self.__model.current_profile_data = None
            self.__model.editing_mode = FormMode.EMPTY
            return
        self.__load_selected_profile_data()
        self.__model.editing_mode = FormMode.VIEW

    def save_profile(self, name, vehicle_type, height, width, depth, weight):
        mode = self.__model.editing_mode
        if not (mode == FormMode.EDIT or mode == FormMode.CREATE):
            return
        if not name or not name.strip():
            self.show_warning.emit("Введите название профиля.")
            return

        try:
            active_profile_changed = False
            changed_active_profile_id = None
            if mode == FormMode.CREATE:
                profile = self.__profile_provider.create_profile(
                    name.strip(), vehicle_type.name, height, width, depth, weight,
                )
            else:
                profile_dto = ProfileDto(
                    self.__model.selected_profile_id, name.strip(), vehicle_type.name, height, width, depth, weight,
                )
                self.__profile_provider.update_profile(self.__model.selected_profile_id, profile_dto)
                active_profile_changed = self.__model.is_active_profile(self.__model.selected_profile_id)
                if active_profile_changed:
                    changed_active_profile_id = self.__model.selected_profile_id

            self.__load_profiles(select_active=False)
            self.__load_selected_profile_data()
            self.__model.editing_mode = FormMode.VIEW
            if active_profile_changed and changed_active_profile_id is not None:
                active_profile = self.__profile_provider.get_profile_by_id(changed_active_profile_id)
                self.active_profile_changed.emit(active_profile)
        except Exception as e:
            self.show_error.emit(f"Ошибка сохранения профиля: {e}")

    @pyqtSlot()
    def request_delete_profile(self):
        """ Запросить подтверждение удаления профиля """
        profile_id = self.__model.selected_profile_id
        if profile_id is None:
            return

        try:
            profile = self.__profile_provider.get_profile_by_id(profile_id)
            if profile is None:
                return

            self.request_delete_confirmation.emit(profile.name)
        except Exception as e:
            self.show_error.emit(f"Ошибка при запросе удаления профиля: {e}")

    def __set_active_profile_id(self, profile_id: int | None):
        self.__service.set_active_profile_id(profile_id)
        self.__model.active_profile_id = profile_id

    def confirm_delete_profile(self):
        """ Подтвержденное удаление профиля """
        try:
            profile_id = self.__model.selected_profile_id
            if profile_id is None:
                return

            if self.__model.is_active_profile(profile_id):
                self.show_error.emit("Нельзя удалить выбранный для расчёта профиль.")
                return

            if self.__model.is_last_profile():
                self.show_error.emit("Нельзя удалить единственный зарегистрированный профиль.")
                return

            self.__profile_provider.delete_profile(profile_id)
            self.__model.selected_profile_id = None
            self.__load_selected_profile_data()
            self.__model.editing_mode = FormMode.EMPTY

            self.__load_profiles()
            self.show_info.emit("Профиль успешно удалён!")
        except Exception as e:
            self.show_error.emit(f"Ошибка удаления профиля: {e}")

    def set_active_profile(self):
        """ Установить текущий профиль как активный """
        profile_id = self.__model.selected_profile_id
        if profile_id is None:
            self.show_info.emit("profile_id is None")
            return

        try:
            self.__set_active_profile_id(profile_id)

            current_profile = self.__model.current_profile_data
            if current_profile:
                self.active_profile_changed.emit(current_profile)
        except Exception as e:
            self.show_error.emit(f"Ошибка установки активного профиля: {e}")
