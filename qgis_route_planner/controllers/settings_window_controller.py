from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from qgis.PyQt.QtCore import QObject, pyqtSignal, pyqtSlot

if TYPE_CHECKING:
    from ..data.models import SettingsModel, FormMode
    from ..services import SettingsService
    from ..data.vehicle import VehicleType, VehicleProfile

from ..data.models import FormMode
from ..data.vehicle import VehicleProfile


class SettingsWindowController(QObject):
    """Контроллер окна настроек"""

    open_page_requested = pyqtSignal(int)
    show_error = pyqtSignal(str)
    show_warning = pyqtSignal(str)
    show_info = pyqtSignal(str)
    request_delete_confirmation = pyqtSignal(str, bool)

    reconnect_requested = pyqtSignal()
    graph_rebuild_requested = pyqtSignal()

    def __init__(
            self,
            model: SettingsModel,
            settings_service: SettingsService,
    ):
        super().__init__()

        self._model = model
        self._service = settings_service

    def open_settings_dialog(self, tab_index: int = 0):
        """Открыть диалог настроек"""
        self._load_initial_state()
        self.open_page_requested.emit(tab_index)

    def _load_initial_state(self):
        """Загрузить начальное состояние"""
        self._load_db_params()
        self._load_profiles()
        self._model.current_profile_id = None
        self._model.current_profile_data = None
        self._model.editing_mode = FormMode.EMPTY

    def _load_db_params(self):
        """Загрузить параметры БД в модель"""
        try:
            db = self._service.load_db_params()
            self._model.db_params = db
        except Exception as e:
            self.show_error.emit(f"Ошибка загрузки параметров подключения к БД: {e}")

    def _load_profiles(self):
        """Загрузить список профилей в модель"""
        try:
            self._model.profiles = self._service.get_profiles()
            self._model.active_profile_id = self._service.get_active_profile_id()
        except Exception as e:
            self.show_error.emit(f"Ошибка загрузки профилей ТС: {e}")

    @pyqtSlot()
    def change_db_connection(self):
        """Запрос на изменение параметров БД"""
        self.reconnect_requested.emit()

    @pyqtSlot()
    def reconnect_with_new_params(self):
        """Переподключение с новыми параметрами (будет вызвано из plugin_controller)"""

        self._load_db_params()
        self.show_info.emit("Параметры подключения к БД обновлены")

    @pyqtSlot()
    def rebuild_graph(self):
        """Запросить перестроение графа"""
        self.graph_rebuild_requested.emit()

    @pyqtSlot()
    def start_profile_create(self):
        """Начать создание нового профиля"""
        self._model.current_profile_id = None
        self._model.current_profile_data = None
        self._model.editing_mode = FormMode.EDIT

    @pyqtSlot()
    def start_profile_edit(self):
        """Начать редактирование текущего профиля"""
        if self._model.current_profile_id is None:
            return
        self._model.editing_mode = FormMode.EDIT

    @pyqtSlot()
    def cancel_profile_edit(self):
        """Отменить редактирование профиля"""
        if self._model.current_profile_id is None:
            self._model.editing_mode = FormMode.EMPTY
            return

        self._load_current_profile_data()
        self._model.editing_mode = FormMode.VIEW

    def _load_current_profile_data(self):
        """Загрузить данные текущего профиля в модель"""
        if self._model.current_profile_id is None:
            self._model.current_profile_data = None
            return
        try:
            profile = self._service.get_profile_by_id(self._model.current_profile_id)
            self._model.current_profile_data = profile
        except Exception as e:
            self.show_error.emit(f"Ошибка загрузки профиля: {e}")
            self._model.current_profile_data = None

    @pyqtSlot(int)
    def select_profile(self, profile_id: Optional[int]):
        """Выбрать профиль для просмотра/редактирования"""
        self._model.current_profile_id = profile_id
        if profile_id is None:
            self._model.current_profile_data = None
            self._model.editing_mode = FormMode.EMPTY
            return

        self._load_current_profile_data()
        self._model.editing_mode = FormMode.VIEW

    @pyqtSlot(str, object, float, float, float, float)
    def save_profile(self, name: str, vehicle_type: VehicleType, height: float, width: float, depth: float,
                     weight: float):
        """Сохранить профиль"""
        if not self._model.is_editing_enabled:
            return

        if not name or not name.strip():
            self.show_warning.emit("Введите название профиля!")
            return

        try:
            profile = VehicleProfile(
                name=name.strip(),
                type=vehicle_type.name,
                height_m=height,
                width_m=width,
                depth_m=depth,
                weight_t=weight,
            )

            if self._model.current_profile_id is None:
                # Создание нового профиля
                profile_id = self._service.create_profile(name.strip(), vehicle_type, height, width, depth, weight)
                self._model.current_profile_id = profile_id
                self.show_info.emit("Профиль успешно создан!")
            else:
                # Обновление существующего
                profile.id = self._model.current_profile_id
                self._service.update_profile(self._model.current_profile_id, profile)
                self.show_info.emit("Профиль успешно обновлен!")

            # Обновить список профилей
            self._load_profiles()
            self._load_current_profile_data()
            self._model.editing_mode = FormMode.VIEW

        except Exception as e:
            self.show_error.emit(f"Ошибка сохранения профиля: {e}")

    @pyqtSlot()
    def request_delete_profile(self):
        """Запросить подтверждение удаления профиля"""
        profile_id = self._model.current_profile_id
        if profile_id is None:
            return

        try:
            profile = self._service.get_profile_by_id(profile_id)
            if profile is None:
                return

            is_active = profile_id == self._model.active_profile_id
            self.request_delete_confirmation.emit(profile.name, is_active)
        except Exception as e:
            self.show_error.emit(f"Ошибка при запросе удаления профиля: {e}")

    @pyqtSlot()
    def confirm_delete_profile(self):
        """Подтвержденное удаление профиля"""
        profile_id = self._model.current_profile_id
        if profile_id is None:
            return

        try:
            is_active = profile_id == self._model.active_profile_id
            if is_active:
                self._service.set_active_profile_id(None)
                self._model.active_profile_id = None

            self._service.delete_profile(profile_id)
            self._model.current_profile_id = None
            self._model.current_profile_data = None
            self._model.editing_mode = FormMode.EMPTY

            self._load_profiles()
            self.show_info.emit("Профиль успешно удалён!")
        except Exception as e:
            self.show_error.emit(f"Ошибка удаления профиля: {e}")

    @pyqtSlot()
    def set_active_profile(self):
        """Установить текущий профиль как активный"""
        profile_id = self._model.current_profile_id
        if profile_id is None:
            return

        if self._model.active_profile_id == profile_id:
            return

        try:
            self._service.set_active_profile_id(profile_id)
            self._model.active_profile_id = profile_id
            self.show_info.emit("Активный профиль изменен")
        except Exception as e:
            self.show_error.emit(f"Ошибка установки активного профиля: {e}")

    def get_active_profile_id(self) -> Optional[int]:
        """Получить ID активного профиля"""
        return self._model.active_profile_id