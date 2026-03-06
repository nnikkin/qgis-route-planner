from qgis.PyQt.QtCore import QObject, pyqtSignal, pyqtSlot

from ..data.models import FormMode, SettingsModel
from ..data.vehicle import VehicleProfile, VehicleType
from ..repositories import DbConnection
from ..services import SettingsService
from ..views import SettingsDialog


class SettingsWindowController(QObject):
    """Контроллер диалога настроек плагина."""

    settings_saved = pyqtSignal(DbConnection)
    profile_changed = pyqtSignal(VehicleProfile)
    profile_deleted = pyqtSignal(int)

    reconnect_requested = pyqtSignal()
    reconnect_cancelled = pyqtSignal()
    graph_rebuild_requested = pyqtSignal()

    def __init__(
            self,
            model: SettingsModel,
            settings_dialog: SettingsDialog,
            settings_service: SettingsService,
    ):
        super().__init__()

        self.__settings_model = model
        self.__settings_dialog = settings_dialog
        self.__settings_service = settings_service

        self.__settings_dialog.set_controller(self)

    def open_settings_dialog(self, tab_index: int = 0):
        self.__initialize()
        self.set_current_tab_active(tab_index)
        self.__settings_dialog.open()

    def close_settings_window(self):
        self.__settings_dialog.close()

    def set_current_tab_active(self, tab_index: int = 0):
        self.__settings_dialog.set_tab_active(tab_index)

    def __initialize(self):
        self.__set_db_form()
        self.__load_profiles()
        self.cancel_profile_edit()

    def __set_db_form(self):
        try:
            db = self.__settings_service.load_db_params()
            if db:
                self.__settings_dialog.set_db_form(db)
            else:
                self.__settings_dialog.show_error("Не удалось загрузить параметры подключения к БД")
        except Exception as e:
            self.__settings_dialog.show_error(f"Ошибка загрузки параметров подключения к БД: {e}")

    def __load_profiles(self):
        try:
            self.__settings_model.active_profile_id = self.__settings_service.get_active_profile_id()
            self.__settings_model.profiles = self.__settings_service.get_profiles()
            self.__emit_active_profile_changed()
        except Exception as e:
            self.__settings_dialog.show_error(f"Произошла ошибка при загрузке профилей ТС: {e}")

    @pyqtSlot()
    def change_db_con_params(self):
        self.reconnect_requested.emit()

    @pyqtSlot()
    def rebuild_graph(self):
        self.graph_rebuild_requested.emit()

    @pyqtSlot()
    def start_profile_create(self):
        self.__settings_model.current_profile_id = None
        self.__settings_dialog.clear_profile_form()
        self.__settings_model.editing_mode = FormMode.EDIT
        self.__settings_dialog.focus_profile_name()

    @pyqtSlot()
    def start_profile_edit(self):
        if self.__settings_model.current_profile_id is None:
            return

        self.__settings_model.editing_mode = FormMode.EDIT
        self.__settings_dialog.focus_profile_name()

    @pyqtSlot()
    def cancel_profile_edit(self):
        profile_id = self.__settings_model.current_profile_id
        if profile_id is None:
            self.__settings_dialog.clear_profile_form()
            self.__settings_model.editing_mode = FormMode.EMPTY
            return

        self.__load_profile_to_form(profile_id)
        self.__settings_model.editing_mode = FormMode.VIEW

    @pyqtSlot(object)
    def select_profile(self, profile_id: int | None):
        self.__settings_model.current_profile_id = profile_id

        if profile_id is None:
            self.__settings_dialog.clear_profile_form()
            self.__settings_model.editing_mode = FormMode.EMPTY
            return

        self.__load_profile_to_form(profile_id)
        self.__settings_model.editing_mode = FormMode.VIEW

    def save_profile(
            self,
            name: str,
            vehicle_type: VehicleType,
            height: float,
            width: float,
            depth: float,
            weight: float,
    ):
        if not self.__settings_model.is_editing_enabled:
            return

        if not name:
            self.__settings_dialog.show_warning("Введите название для профиля!")
            return

        try:
            current_profile_id = self.__settings_model.current_profile_id
            profile = VehicleProfile(
                name=name,
                type=vehicle_type.name if isinstance(vehicle_type, VehicleType) else vehicle_type,
                height_m=height,
                width_m=width,
                depth_m=depth,
                weight_t=weight,
            )

            if current_profile_id is None:
                new_profile_id = self.__settings_service.create_profile(
                    name,
                    vehicle_type,
                    height,
                    width,
                    depth,
                    weight,
                )
                self.__settings_model.current_profile_id = new_profile_id
                message = "Профиль успешно создан!"
            else:
                self.__settings_service.update_profile(current_profile_id, profile)
                message = "Профиль успешно обновлен!"

            self.__load_profiles()
            self.__settings_model.editing_mode = FormMode.VIEW
            self.__settings_dialog.show_info(message)
        except Exception as e:
            self.__settings_dialog.show_error(f"Ошибка сохранения профиля: {e}")

    @pyqtSlot()
    def delete_profile(self):
        profile_id = self.__settings_model.current_profile_id
        if profile_id is None:
            return

        profile = self.__settings_service.get_profile_by_id(profile_id)
        if profile is None:
            self.cancel_profile_edit()
            return

        is_active = profile_id == self.__settings_model.active_profile_id
        if not self.__settings_dialog.confirm_delete_profile(profile.name, is_active):
            return

        try:
            self.__settings_service.delete_profile(profile_id)

            if is_active:
                self.__settings_service.set_active_profile_id(None)
                self.__settings_model.active_profile_id = None
                self.profile_deleted.emit(profile_id)

            self.__settings_model.current_profile_id = None
            self.__settings_dialog.clear_profile_form()
            self.__settings_model.editing_mode = FormMode.EMPTY
            self.__load_profiles()
            self.__settings_dialog.show_info("Профиль успешно удален!")
        except Exception as e:
            self.__settings_dialog.show_error(f"Ошибка удаления профиля: {e}")

    @pyqtSlot(object)
    def set_active_profile(self, profile_id: int | None):
        if profile_id is None or self.__settings_model.active_profile_id == profile_id:
            return

        self.__settings_service.set_active_profile_id(profile_id)
        self.__settings_model.active_profile_id = profile_id
        self.__emit_active_profile_changed()

    def __load_profile_to_form(self, profile_id: int):
        try:
            profile = self.__settings_service.get_profile_by_id(profile_id)
            if profile is None:
                self.select_profile(None)
                return

            self.__settings_dialog.set_profile_form(profile)
        except Exception as e:
            self.__settings_dialog.show_error(f"Произошла ошибка при загрузке профиля ТС: {e}")

    def __emit_active_profile_changed(self):
        active_profile_id = self.__settings_model.active_profile_id
        if active_profile_id is None:
            return

        profile = self.__settings_service.get_profile_by_id(active_profile_id)
        if profile is not None:
            self.profile_changed.emit(profile)
