from __future__ import annotations

from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsTask, QgsApplication

from ..repositories import (
    RoadGraphRepository,
    LayerRepository,
    VehicleProfileRepository,
    RestrictionRepository,
    DbConnection,
)
from ..services import (
    SpatialDataService,
    RoutingService,
    SettingsService,
    RestrictionService
)
from ..data.models import (
    DbConfigModel,
    LayerConfigModel,
    ColumnsConfigModel,
    SettingsModel,
    MainWindowModel,
    RestrictionModel
)

from .base_controller import BaseController
from .init_dialogs_controller import InitDialogsController
from .main_window_controller import MainWindowController
from .settings_dialog_controller import SettingsDialogController
from .restriction_dialog_controller import RestrictionDialogController

from ..views import (
    PluginMainWindow,
    ConnectionConfigDialog,
    SettingsDialog,
    LayersSelectDialog,
    LayerColumnsDialog,
    RestrictionDialog
)


class PluginController(BaseController):
    """Контроллер плагина"""

    plugin_initialized = pyqtSignal()
    crit_plugin_error = pyqtSignal()

    def __init__(self):
        super().__init__(parent=None)

        self.__build_task = None
        self.__rebuild_task = None

        self.__db_config_model: DbConfigModel = DbConfigModel()
        self.__layers_config_model: LayerConfigModel = LayerConfigModel()
        self.__cols_config_model: ColumnsConfigModel = ColumnsConfigModel()
        self.__settings_model: SettingsModel = SettingsModel()
        self.__main_window_model: MainWindowModel = MainWindowModel()
        self.__restriction_model: RestrictionModel = RestrictionModel()

        self.__main_window_controller: MainWindowController | None = None
        self.__settings_controller: SettingsDialogController | None = None
        self.__restriction_controller: RestrictionDialogController | None = None
        self.__init_dialogs_controller: InitDialogsController = InitDialogsController(
            db_config_model=self.__db_config_model,
            layer_config_model=self.__layers_config_model,
            columns_config_model=self.__cols_config_model
        )

        self.__db_config_dialog: ConnectionConfigDialog = ConnectionConfigDialog(
            model=self.__db_config_model,
            controller=self.__init_dialogs_controller,
        )
        self.__layer_select_dialog: LayersSelectDialog = LayersSelectDialog(
            model=self.__layers_config_model,
            controller=self.__init_dialogs_controller,
        )
        self.__cols_config_dialog: LayerColumnsDialog = LayerColumnsDialog(
            model=self.__cols_config_model,
            controller=self.__init_dialogs_controller,
        )
        self.__main_window: PluginMainWindow | None = None
        self.__restriction_dialog: RestrictionDialog | None = None
        self.__settings_dialog: SettingsDialog | None = None

        self.__db_connection: DbConnection | None = None

        self.__settings_service: SettingsService | None = None
        self.__spatial_data_service: SpatialDataService | None = None
        self.__routing_service: RoutingService | None = None
        self.__restriction_service: RestrictionService | None = None

        self.__vehicle_repo: VehicleProfileRepository | None = None
        self.__layer_repo: LayerRepository | None = None
        self.__graph_repo: RoadGraphRepository | None = None
        self.__restriction_repo: RestrictionRepository | None = None

        self.__old_db_connection: DbConnection | None = None
        self.__old_db_config_model: DbConfigModel | None = None
        self.__old_layers_config_model: LayerConfigModel | None = None
        self.__old_cols_config_model: ColumnsConfigModel | None = None
        self.__old_restriction_model: RestrictionModel | None = None

        self.__connect()

    def first_start_initialize(self):
        self.__db_config_dialog.open()

    def open_main_window(self):
        self.__main_window.show()

    def __connect(self):
        self.__init_dialogs_controller.con_test_requested.connect(self.__db_con_test)
        self.__init_dialogs_controller.con_params_obtained.connect(self.__db_con_created)
        self.__init_dialogs_controller.layers_selected.connect(self.__layers_selected)
        self.__init_dialogs_controller.columns_configured.connect(self.__columns_configured)
        self.__init_dialogs_controller.init_cancelled.connect(self.__initialization_cancelled)

    def __init_views(self):
        self.__main_window = PluginMainWindow(
            model=self.__main_window_model,
            controller=self.__main_window_controller
        )
        self.__settings_dialog = SettingsDialog(
            model=self.__settings_model,
            controller=self.__settings_controller
        )
        self.__restriction_dialog = RestrictionDialog(
            model=self.__restriction_model,
            controller=self.__restriction_controller
        )

    def __init_controllers(self):
        self.__settings_controller = SettingsDialogController(
            self.__settings_model,
            self.__settings_service
        )
        self.__settings_controller.reconnect_requested.connect(self.__on_reconnect_requested)
        self.__settings_controller.graph_rebuild_requested.connect(self.__on_graph_rebuild_requested)

        self.__restriction_controller = RestrictionDialogController(
            self.__restriction_model,
            self.__restriction_service
        )

        self.__main_window_controller = MainWindowController(
            model=self.__main_window_model,
            settings_controller=self.__settings_controller,
            restr_controller=self.__restriction_controller,
            data_service=self.__spatial_data_service,
            routing_service=self.__routing_service,
        )

        self.__settings_controller.active_profile_changed.connect(
            self.__main_window_controller.update_active_profile
        )

    def __init_repositories(self):
        self.__vehicle_repo = VehicleProfileRepository(self.__db_connection)
        self.__layer_repo = LayerRepository(self.__db_connection)
        self.__graph_repo = RoadGraphRepository(self.__db_connection, self.__layer_repo)
        self.__restriction_repo = RestrictionRepository(self.__db_connection)

    def __init_services(self):
        self.__settings_service = SettingsService(self.__vehicle_repo)
        self.__spatial_data_service = SpatialDataService(
            self.__layer_repo,
            self.__graph_repo,
            self.__vehicle_repo,
            self.__restriction_repo,
        )
        self.__routing_service = RoutingService(self.__graph_repo)
        self.__restriction_service = RestrictionService(self.__restriction_repo)

    def __init_everything(self):
        self.__init_repositories()
        self.__init_services()
        self.__init_controllers()
        self.__init_views()

    def __db_con_test(self):
        try:
            self.__db_connection = DbConnection(
                host=self.__db_config_model.host,
                port=self.__db_config_model.port,
                username=self.__db_config_model.username,
                password=self.__db_config_model.password,
                database=self.__db_config_model.database,
                schema=self.__db_config_model.schema,
            )
            if self.__db_connection.test_connection():
                self.__init_repositories()
                self.__init_services()
                self.__init_dialogs_controller.set_service(self.__spatial_data_service)
        except Exception as e:
            QMessageBox.critical(None, "Ошибка",
                f"Не удалось завершить инициализацию плагина:\n{e}", QMessageBox.Ok)

    def __db_con_created(self):
        try:
            self.__db_connection = DbConnection(
                host=self.__db_config_model.host,
                port=self.__db_config_model.port,
                username=self.__db_config_model.username,
                password=self.__db_config_model.password,
                database=self.__db_config_model.database,
                schema=self.__db_config_model.schema,
            )
            if self.__main_window_controller and self.__settings_controller:
                self.__main_window.close()
                self.__settings_dialog.close()

            self.__init_everything()
            self.__settings_service.save_db_params(self.__db_connection)
            self.__layer_select_dialog.open()
        except Exception as e:
            QMessageBox.critical(None, "Ошибка",
                f"Не удалось завершить инициализацию плагина:\n{e}", QMessageBox.Ok)

    def __layers_selected(self):
        self.__selected_layers = self.__layers_config_model.selected_layers
        self.__cols_config_dialog.open()

    def __columns_configured(self):
        self.__column_mapping = self.__cols_config_model.mappings
        self.__initialization_finished()

    def __initialization_finished(self):
        selected_layers = list(self.__selected_layers)
        column_mapping = dict(self.__column_mapping)

        try:
            def run_in_background(task: QgsTask):
                task.setProgress(0)
                self.__spatial_data_service.run_init_database(selected_layers, column_mapping)
                task.setProgress(100)
                return True

            def on_finished(exception, result=None):
                if exception:
                    QMessageBox.critical(None, "Ошибка",
                        f"Не удалось инициализировать БД:\n{exception}", QMessageBox.Ok)
                    return
                self.__on_topology_build_finished()

            self.__build_task = QgsTask.fromFunction(
                "Инициализация базы данных",
                run_in_background,
                on_finished=on_finished,
            )
            QgsApplication.taskManager().addTask(self.__build_task)
        except Exception as e:
            QMessageBox.critical(None, "Ошибка",
                f"Не удалось построить граф:\n{e}\nПлагин завершает работу.", QMessageBox.Ok)
            self.crit_plugin_error.emit()

    def __on_topology_build_finished(self):
        self.plugin_initialized.emit()
        self.__initialize_map()

    def __on_topology_rebuild_finished(self):
        self.__initialize_map()
        self.__settings_dialog.close()

    def __initialization_cancelled(self):
        if self.__main_window_controller:
            self.__main_window.close()
        self.__init_dialogs_controller = None

    def __initialize_map(self):
        self.__main_window_controller.initialize_map()
        self.__main_window.show()

    def __on_graph_rebuild_requested(self):
        self.__main_window.close()
        try:
            def run_in_background(task: QgsTask):
                task.setProgress(0)
                self.__graph_repo.create_topology()
                task.setProgress(100)
                return True

            def on_finished(exception, result=None):
                if exception:
                    QMessageBox.critical(None, "Ошибка",
                        f"Не удалось инициализировать БД:\n{exception}", QMessageBox.Ok)
                    return
                self.__on_topology_rebuild_finished()

            self.__rebuild_task = QgsTask.fromFunction(
                "Пересоздание графа",
                run_in_background,
                on_finished=on_finished,
            )
            QgsApplication.taskManager().addTask(self.__rebuild_task)
        except Exception as e:
            QMessageBox.critical(None, "Ошибка",
                f"Не удалось перестроить граф:\n{e}", QMessageBox.Ok)

    def __on_reconnect_requested(self):
        self.__old_db_connection = self.__db_connection
        self.__old_db_config_model = self.__db_config_model
        self.__old_layers_config_model = self.__layers_config_model
        self.__old_cols_config_model = self.__cols_config_model
        self.__old_restriction_model = self.__restriction_model
        try:
            self.__db_config_dialog.open()
        except Exception as e:
            QMessageBox.critical(None, "Ошибка",
                f"Во время переподключения произошла ошибка:\n{e}", QMessageBox.Ok)
            self.__reconnect_cancelled()

    def __reconnect_cancelled(self):
        self.__db_connection = self.__old_db_connection
        self.__db_config_model = self.__old_db_config_model
        self.__layers_config_model = self.__old_layers_config_model
        self.__cols_config_model = self.__old_cols_config_model
        self.__restriction_model = self.__old_restriction_model
        self.__old_db_connection = None
        self.__old_db_config_model = None
        self.__old_layers_config_model = None
        self.__old_cols_config_model = None
        self.__old_restriction_model = None

    def unload(self):
        if self.__main_window_controller is not None:
            self.__main_window_controller.on_clear_everything()