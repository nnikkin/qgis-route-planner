from qgis.PyQt.QtCore import QObject, pyqtSignal, Qt
from qgis.PyQt.QtWidgets import QListWidgetItem, QMessageBox

from qgis_route_planner.controllers.init_dialogs_controller import InitDialogsController
from qgis_route_planner.models.vehicle.vehicle_profile import VehicleProfile
from qgis_route_planner.models.vehicle.vehicle_type import VehicleType
from qgis_route_planner.repositories.db_connection import DbConnection
from qgis_route_planner.services.settings_service import SettingsService
from qgis_route_planner.views.settings_view import SettingsDialog


class SettingsWindowController(QObject):
    """Контроллер диалога настроек плагина."""

    settings_saved = pyqtSignal(DbConnection)
    profile_changed = pyqtSignal(VehicleProfile)
    reconnect_requested = pyqtSignal(InitDialogsController)
    graph_rebuild_requested = pyqtSignal()

    def __init__(self, settings_service: SettingsService):
        super().__init__()
        self.__settings_service = settings_service

        self.__active_profile_id = None
        self.__current_profile_id = None

        self.__settings_dialog = SettingsDialog()
        self.__connect_signals()
        self.__initialize()

    def __connect_signals(self):
        self.__settings_dialog.editDbConButton.clicked.connect(self.__on_edit_db_con_button_click)

        self.__settings_dialog.saveProfileButton.clicked.connect(self.__save_profile)
        self.__settings_dialog.deleteProfileButton.clicked.connect(self.__delete_profile)
        self.__settings_dialog.editProfileButton.clicked.connect(self.__edit_profile)
        self.__settings_dialog.cancelProfileEditButton.clicked.connect(self.__cancel_edit)
        self.__settings_dialog.createProfileButton.clicked.connect(self.__create_new_profile)
        self.__settings_dialog.profilesListWidget.itemSelectionChanged.connect(self.__on_profile_selected)
        self.__settings_dialog.setActiveProfileButton.clicked.connect(self.__set_active_profile)
        self.__settings_dialog.profilesListWidget.itemDoubleClicked.connect(self.__on_profile_double_clicked)

        self.__settings_dialog.rebuildGraphButton.clicked.connect(self.__on_rebuild_graph_button_click)

    def __initialize(self):
        self.__set_db_form()
        self.__cancel_edit()
        self.__load_profiles()

    def open_settings_dialog(self, tab_index: int = 0):
        self.set_current_tab_active(tab_index)
        self.__settings_dialog.exec()

    def close_settings_window(self):
        self.__settings_dialog.accept()
        print("the old one should be closed")

    def set_current_tab_active(self, tab_index: int = 0):
        self.__settings_dialog.set_tab_active(tab_index)


    # Работа с профилями ТС
    def __set_profile_mode(self, mode: str):
        is_edit_mode = mode == "edit"
        has_selection = mode == "view"

        self.__enable_profile_form(is_edit_mode)
        self.__settings_dialog.saveProfileButton.setEnabled(is_edit_mode)
        self.__settings_dialog.cancelProfileEditButton.setEnabled(is_edit_mode)
        self.__settings_dialog.editProfileButton.setEnabled(has_selection)
        self.__settings_dialog.deleteProfileButton.setEnabled(has_selection)
        self.__settings_dialog.setActiveProfileButton.setEnabled(has_selection)

    def __set_active_profile(self, item=None):
        if item is None:
            selected_items = self.__settings_dialog.profilesListWidget.selectedItems()
            if not selected_items:
                return
            item = selected_items[0]

        profile_id = item.data(Qt.ItemDataRole.UserRole)
        if self.__active_profile_id == profile_id:
            return

        self.__active_profile_id = profile_id
        self.__settings_service.set_active_profile_id(profile_id)
        self.__update_profiles_list_display()
        self.__emit_active_profile_changed()

    def __emit_active_profile_changed(self):
        if self.__active_profile_id is None:
            return

        profile = self.__settings_service.get_profile_by_id(self.__active_profile_id)
        self.profile_changed.emit(profile)

    def __create_new_profile(self):
        self.__current_profile_id = None
        self.__clear_profile_form()
        self.__settings_dialog.profilesListWidget.clearSelection()
        self.__set_profile_mode("edit")
        self.__settings_dialog.profileNameEdit.setFocus()

    def __edit_profile(self):
        if self.__current_profile_id is None:
            return
        self.__set_profile_mode("edit")
        self.__settings_dialog.profileNameEdit.setFocus()

    def __save_profile(self):
        name = self.__settings_dialog.profileNameEdit.text().strip()
        if not name:
            QMessageBox.warning(
                self.__settings_dialog,
                "",
                "Введите название профиля!",
                QMessageBox.Ok,
            )
            return

        profile = VehicleProfile(
            name=name,
            type=self.__settings_dialog.vehicleTypeComboBox.currentData(),
            height_m=self.__settings_dialog.profileHeightSpinBox.value(),
            width_m=self.__settings_dialog.profileWidthSpinBox.value(),
            depth_m=self.__settings_dialog.profileDepthSpinBox.value(),
            weight_t=self.__settings_dialog.profileWeightSpinBox.value(),
            max_speed_kmh=self.__settings_dialog.profileSpeedSpinBox.value(),
        )

        try:
            if self.__current_profile_id is not None:
                self.__settings_service.update_profile(self.__current_profile_id, profile)
                message = "Профиль успешно обновлен!"
            else:
                self.__settings_service.create_profile(profile)
                message = "Профиль успешно создан!"

            self.__load_profiles()
            self.__cancel_edit()
            QMessageBox.information(self.__settings_dialog, "", message, QMessageBox.Ok)
        except Exception as e:
            QMessageBox.critical(
                self.__settings_dialog,
                "",
                f"Ошибка сохранения профиля: {str(e)}",
                QMessageBox.Ok,
            )

    def __delete_profile(self):
        if self.__current_profile_id is None:
            return

        reply = QMessageBox.question(
            self.__settings_dialog,
            "",
            f"Вы уверены, что хотите удалить профиль '{self.__settings_dialog.profileNameEdit.text()}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            profile_id_to_delete = self.__current_profile_id
            self.__settings_service.delete_profile(profile_id_to_delete)

            if self.__active_profile_id == profile_id_to_delete:
                self.__active_profile_id = None
                self.profile_changed.emit(None)

            self.__load_profiles()
            self.__cancel_edit()
            QMessageBox.information(self.__settings_dialog, "", "Профиль успешно удален!", QMessageBox.Ok)
        except Exception as e:
            QMessageBox.critical(
                self.__settings_dialog,
                "",
                f"Ошибка удаления профиля: {str(e)}",
                QMessageBox.Ok,
            )


    # Работа со списком профилей
    def __on_profile_selected(self):
        selected_items = self.__settings_dialog.profilesListWidget.selectedItems()
        if not selected_items:
            self.__cancel_edit()
            return

        profile_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self.__current_profile_id = profile_id
        self.__load_profile_to_form(profile_id)
        self.__set_profile_mode("view")

    def __on_profile_double_clicked(self, item):
        self.__set_active_profile(item)

    def __update_profiles_list_display(self):
        for i in range(self.__settings_dialog.profilesListWidget.count()):
            item = self.__settings_dialog.profilesListWidget.item(i)
            profile_id = item.data(Qt.ItemDataRole.UserRole)
            original_name = item.data(Qt.ItemDataRole.UserRole + 1)
            is_active = profile_id == self.__active_profile_id

            font = item.font()
            font.setBold(is_active)
            item.setFont(font)
            item.setText(f"★ {original_name}" if is_active else original_name)

    def __load_profile_to_form(self, profile_id: int):
        try:
            profile = self.__settings_service.get_profile_by_id(profile_id)
            if not profile:
                self.__cancel_edit()
                return

            self.__settings_dialog.profileNameEdit.setText(profile.name)

            index = self.__settings_dialog.vehicleTypeComboBox.findData(profile.type)
            if index >= 0:
                self.__settings_dialog.vehicleTypeComboBox.setCurrentIndex(index)

            self.__settings_dialog.profileHeightSpinBox.setValue(profile.height_m)
            self.__settings_dialog.profileWidthSpinBox.setValue(profile.width_m)
            self.__settings_dialog.profileWeightSpinBox.setValue(profile.weight_t)
            self.__settings_dialog.profileDepthSpinBox.setValue(profile.depth_m)
            self.__settings_dialog.profileSpeedSpinBox.setValue(profile.max_speed_kmh)
        except Exception as e:
            print(f"Error loading profile: {e}")

    def __load_profiles(self):
        try:
            profiles = self.__settings_service.get_all_profiles()
            self.__settings_dialog.profilesListWidget.clear()

            self.__active_profile_id = self.__settings_service.get_active_profile_id()

            for profile in profiles:
                display_name = f"{profile.name}"
                item = QListWidgetItem(display_name)
                item.setData(Qt.ItemDataRole.UserRole, profile.id)
                item.setData(Qt.ItemDataRole.UserRole + 1, display_name)
                self.__settings_dialog.profilesListWidget.addItem(item)

            self.__update_profiles_list_display()
            self.__emit_active_profile_changed()
        except Exception as e:
            print(f"Error loading profiles: {e}")


    # Вспомогательное для форм
    def __clear_profile_form(self):
        self.__settings_dialog.profileNameEdit.clear()
        self.__settings_dialog.vehicleTypeComboBox.setCurrentIndex(0)
        self.__settings_dialog.profileHeightSpinBox.setValue(0)
        self.__settings_dialog.profileWidthSpinBox.setValue(0)
        self.__settings_dialog.profileWeightSpinBox.setValue(0)
        self.__settings_dialog.profileDepthSpinBox.setValue(0)
        self.__settings_dialog.profileSpeedSpinBox.setValue(0)

    def __enable_profile_form(self, enabled: bool):
        self.__settings_dialog.profileNameEdit.setEnabled(enabled)
        self.__settings_dialog.vehicleTypeComboBox.setEnabled(enabled)
        self.__settings_dialog.profileHeightSpinBox.setEnabled(enabled)
        self.__settings_dialog.profileWidthSpinBox.setEnabled(enabled)
        self.__settings_dialog.profileDepthSpinBox.setEnabled(enabled)
        self.__settings_dialog.profileWeightSpinBox.setEnabled(enabled)
        self.__settings_dialog.profileSpeedSpinBox.setEnabled(enabled)

    def __cancel_edit(self):
        self.__current_profile_id = None
        self.__clear_profile_form()
        self.__set_profile_mode("empty")
        self.__settings_dialog.profilesListWidget.clearSelection()


    # Работа с настройками БД
    def __set_db_form(self):
        try:
            s = self.__settings_service.load_db_params()
            if not s:
                QMessageBox.critical(
                    self.__settings_dialog,
                    "Ошибка",
                    "Не удалось загрузить параметры подключения к БД",
                    QMessageBox.Ok
                )
                return

            self.__settings_dialog.dbHostnameEdit.setText(s.host)
            self.__settings_dialog.dbPortEdit.setText(str(s.port))
            self.__settings_dialog.dbUsernameEdit.setText(s.username)
            self.__settings_dialog.dbPasswordEdit.setText(s.password)
            self.__settings_dialog.dbDatabaseNameEdit.setText(s.database)
            self.__settings_dialog.dbSchemaEdit.setText(s.schema)
        except Exception as e:
            print(e)

    def __on_edit_db_con_button_click(self):
        question = QMessageBox.question(
            self.__settings_dialog,
            "",
            "Вы точно хотите изменить настройки подключения к базе данных?",
            QMessageBox.Yes | QMessageBox.No
        )

        if question == QMessageBox.Yes:
            init_ctrl = InitDialogsController()
            self.reconnect_requested.emit(init_ctrl)
            init_ctrl.start_init_process()

    # Работа с графом
    def __on_rebuild_graph_button_click(self):
        question = QMessageBox.question(
            self.__settings_dialog,
            "",
            "Вы точно хотите перестроить граф дорог?",
            QMessageBox.Yes | QMessageBox.No
        )

        if question == QMessageBox.Yes:
            self.graph_rebuild_requested.emit()