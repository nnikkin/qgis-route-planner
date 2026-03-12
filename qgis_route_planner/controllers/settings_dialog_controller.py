from __future__ import annotations

from typing import TYPE_CHECKING

from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot

if TYPE_CHECKING:
    from ..data.models import SettingsModel, FormMode
    from ..services import SettingsService
    from ..data.vehicle import VehicleType, VehicleProfile

from ..data.models import FormMode
from ..data.vehicle import VehicleProfile
from ..controllers import BaseController


class SettingsDialogController(BaseController):
    """Контроллер окна настроек"""

    open_page_requested = pyqtSignal(int)
    request_delete_confirmation = pyqtSignal(str, bool)

    reconnect_requested = pyqtSignal()
    graph_rebuild_requested = pyqtSignal()

    def __init__(
            self,
            model: SettingsModel,
            settings_service: SettingsService,
    ):
        super().__init__()

        self.__model = model
        self.__service = settings_service

    def open_dialog_tab(self, tab_index: int = 0):
        """Открыть диалог настроек"""
        self.__load_initial_state()
        self.open_page_requested.emit(tab_index)

    def __load_initial_state(self):
        """Загрузить начальное состояние"""
        self.__load_db_params()
        self.__load_profiles()
        self.__model.current_profile_id = None
        self.__model.current_profile_data = None
        self.__model.editing_mode = FormMode.EMPTY

    def __load_db_params(self):
        """Загрузить параметры БД в модель"""
        try:
            db = self.__service.load_db_params()
            self.__model.db_params = db
        except Exception as e:
            self.show_error.emit(f"Ошибка загрузки параметров подключения к БД: {e}")

    def __load_profiles(self):
        """Загрузить список профилей в модель"""
        try:
            self.__model.profiles = self.__service.get_profiles()
            self.__model.active_profile_id = self.__service.get_active_profile_id()
        except Exception as e:
            self.show_error.emit(f"Ошибка загрузки профилей ТС: {e}")

    @pyqtSlot()
    def change_db_connection(self):
        """Запрос на изменение параметров БД"""
        self.reconnect_requested.emit()

    @pyqtSlot()
    def reconnect_with_new_params(self):
        """Переподключение с новыми параметрами (будет вызвано из plugin_controller)"""

        self.__load_db_params()
        self.show_info.emit("Параметры подключения к БД обновлены")

    @pyqtSlot()
    def rebuild_graph(self):
        """Запросить перестроение графа"""
        self.graph_rebuild_requested.emit()

    @pyqtSlot()
    def start_profile_create(self):
        """Начать создание нового профиля"""
        self.__model.current_profile_id = None
        self.__model.current_profile_data = None
        self.__model.editing_mode = FormMode.CREATE

    @pyqtSlot()
    def start_profile_edit(self):
        """Начать редактирование текущего профиля"""
        if self.__model.current_profile_id is None:
            return
        self.__model.editing_mode = FormMode.EDIT

    @pyqtSlot()
    def cancel_profile_edit(self):
        """Отменить редактирование профиля"""
        if self.__model.current_profile_id is None:
            self.__model.editing_mode = FormMode.EMPTY
            return

        self.__load_current_profile_data()
        self.__model.editing_mode = FormMode.VIEW

    def __load_current_profile_data(self):
        """Загрузить данные текущего профиля в модель"""
        if self.__model.current_profile_id is None:
            self.__model.current_profile_data = None
            return
        try:
            profile = self.__service.get_profile_by_id(self.__model.current_profile_id)
            self.__model.current_profile_data = profile
        except Exception as e:
            self.show_error.emit(f"Ошибка загрузки профиля: {e}")
            self.__model.current_profile_data = None

    @pyqtSlot(int)
    def select_profile(self, profile_id: int):
        """Выбрать профиль для просмотра/редактирования"""
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
        """Сохранить профиль"""
        mode = self.__model.editing_mode
        if not (mode == FormMode.EDIT or mode == FormMode.CREATE):
            return

        if not name or not name.strip():
            self.show_warning.emit("Введите название профиля!")
            return

        try:
            if mode == FormMode.CREATE:
                # Создание нового профиля
                profile_id = self.__service.create_profile(name.strip(), vehicle_type, height, width, depth, weight)
                self.__model.current_profile_id = profile_id
                self.show_info.emit("Профиль успешно создан!")
            else:
                # Обновление существующего
                profile = VehicleProfile(
                    name=name.strip(),
                    type=vehicle_type.name,
                    height_m=height,
                    width_m=width,
                    depth_m=depth,
                    weight_t=weight,
                )
                profile.id = self.__model.current_profile_id
                self.__service.update_profile(self.__model.current_profile_id, profile)
                self.show_info.emit("Профиль успешно обновлен!")

            # Обновить список профилей
            self.__load_profiles()
            self.__load_current_profile_data()
            self.__model.editing_mode = FormMode.VIEW

        except Exception as e:
            self.show_error.emit(f"Ошибка сохранения профиля: {e}")

    @pyqtSlot()
    def request_delete_profile(self):
        """Запросить подтверждение удаления профиля"""
        profile_id = self.__model.current_profile_id
        if profile_id is None:
            return

        try:
            profile = self.__service.get_profile_by_id(profile_id)
            if profile is None:
                return

            is_active = profile_id == self.__model.active_profile_id
            self.request_delete_confirmation.emit(profile.name, is_active)
        except Exception as e:
            self.show_error.emit(f"Ошибка при запросе удаления профиля: {e}")

    @pyqtSlot()
    def confirm_delete_profile(self):
        """Подтвержденное удаление профиля"""
        try:
            profile_id = self.__model.current_profile_id
            if profile_id is None:
                return

            if len(self.__model.profiles)-1 <= 0:
                raise BaseException("Нельзя удалить единственный зарегистрированный профиль")

            is_active = profile_id == self.__model.active_profile_id
            if is_active:
                self.__service.set_active_profile_id(None)
                self.__model.active_profile_id = None

            self.__service.delete_profile(profile_id)
            self.__model.current_profile_id = None
            self.__model.current_profile_data = None
            self.__model.editing_mode = FormMode.EMPTY

            self.__load_profiles()
            self.show_info.emit("Профиль успешно удалён!")
        except Exception as e:
            self.show_error.emit(f"Ошибка удаления профиля: {e}")

    @pyqtSlot()
    def set_active_profile(self):
        """Установить текущий профиль как активный"""
        profile_id = self.__model.current_profile_id
        if profile_id is None:
            return

        if self.__model.active_profile_id == profile_id:
            return

        try:
            self.__service.set_active_profile_id(profile_id)
            self.__model.active_profile_id = profile_id
            self.show_info.emit("Активный профиль изменен")
        except Exception as e:
            self.show_error.emit(f"Ошибка установки активного профиля: {e}")

    def get_active_profile_id(self) -> int:
        """Получить ID активного профиля"""
        return self.__model.active_profile_id