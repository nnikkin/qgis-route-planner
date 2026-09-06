from __future__ import annotations

import copy

from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot, QObject
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsTask, QgsApplication
from qgis.utils import iface

from qgis_route_planner.logger import Logger
from qgis_route_planner.exceptions import PluginError
from qgis_route_planner.core.db_connection import DbConnection

from qgis_route_planner.main import MainWindowModel, MainWindowController, MainWindow
from qgis_route_planner.layer_config import (
    RoadGraphRepository,
    LayerRepository,
    SpatialDataService,
    LayerConfigModel,
    ColumnsConfigModel,
    LayersSelectDialog,
    LayerColumnsDialog,
    LayerDialogsController
)
from qgis_route_planner.db_con_init import (
    ConnectionConfigDialog,
    DbInitController,
    DbConfigModel
)
from qgis_route_planner.settings import (
    SettingsDialog,
    SettingsDialogController,
    SettingsModel,
    SettingsService
)
from qgis_route_planner.restrictions import (
    RestrictionDialog,
    RestrictionDialogController,
    RestrictionModel,
    RestrictionRepository,
    RestrictionService
)
from qgis_route_planner.routing import RoutingService, WeatherService
from qgis_route_planner.vehicle import VehicleProfileRepository, VehicleService


class PluginCoordinator(QObject):
    """ Контроллер плагина """

    plugin_initialized = pyqtSignal()
    plugin_init_cancelled = pyqtSignal()
    crit_plugin_error = pyqtSignal()

    show_error = pyqtSignal(str)
    show_warning = pyqtSignal(str)
    show_info = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.__build_task = None
        self.__rebuild_task = None
        self.__is_initialized = False

        self.__db_config_model: DbConfigModel = DbConfigModel()
        self.__layers_config_model: LayerConfigModel = LayerConfigModel()
        self.__cols_config_model: ColumnsConfigModel = ColumnsConfigModel()
        self.__settings_model: SettingsModel = SettingsModel()
        self.__main_window_model: MainWindowModel = MainWindowModel()
        self.__restriction_model: RestrictionModel = RestrictionModel()

        self.__main_window_controller: MainWindowController | None = None
        self.__settings_controller: SettingsDialogController | None = None
        self.__restriction_controller: RestrictionDialogController | None = None
        self.__db_config_controller: DbInitController = DbInitController(
            model=self.__db_config_model
        )
        self.__layer_dialogs_controller: LayerDialogsController = LayerDialogsController(
            layer_config_model=self.__layers_config_model,
            columns_config_model=self.__cols_config_model
        )

        self.__db_config_dialog: ConnectionConfigDialog = ConnectionConfigDialog(
            model=self.__db_config_model,
            controller=self.__db_config_controller,
        )
        self.__layer_select_dialog: LayersSelectDialog = LayersSelectDialog(
            model=self.__layers_config_model,
            controller=self.__layer_dialogs_controller,
        )
        self.__cols_config_dialog: LayerColumnsDialog = LayerColumnsDialog(
            model=self.__cols_config_model,
            controller=self.__layer_dialogs_controller,
        )
        self.__main_window: MainWindow | None = None
        self.__restriction_dialog: RestrictionDialog | None = None
        self.__settings_dialog: SettingsDialog | None = None

        self.__db_connection: DbConnection | None = None

        self.__settings_service: SettingsService = SettingsService()
        self.__spatial_data_service: SpatialDataService | None = None
        self.__routing_service: RoutingService | None = None
        self.__restriction_service: RestrictionService | None = None
        self.__weather_service: WeatherService | None = None
        self.__vehicle_service: VehicleService | None = None

        self.__vehicle_repo: VehicleProfileRepository | None = None
        self.__layer_repo: LayerRepository | None = None
        self.__graph_repo: RoadGraphRepository | None = None
        self.__restriction_repo: RestrictionRepository | None = None

        self.__old_db_connection: DbConnection | None = None
        self.__old_db_config_model: DbConfigModel | None = None
        self.__old_layers_config_model: LayerConfigModel | None = None
        self.__old_cols_config_model: ColumnsConfigModel | None = None
        self.__old_restriction_model: RestrictionModel | None = None
        self.__is_reconnecting = False
        self.__reconnect_snapshot: dict[str, object] | None = None

        self.__connect()

    def first_start_initialize(self):
        Logger.info("Начата инициализация плагина")

        self.__is_initialized = False
        self.__load_saved_db_params()
        self.__db_config_dialog.open()

    def __load_saved_db_params(self):
        try:
            saved_params = self.__settings_service.load_db_params()
            if saved_params and saved_params.has_required_params():
                self.__db_config_model.host = saved_params.host
                self.__db_config_model.port = saved_params.port
                self.__db_config_model.database = saved_params.database
                self.__db_config_model.username = saved_params.username
                self.__db_config_model.password = saved_params.password
        except Exception as e:
            QMessageBox.critical(f"Не удалось загрузить сохранённые параметры подключения: {e}")
            Logger.warning(f"Не удалось загрузить сохранённые параметры подключения: {e}")

    def open_main_window(self):
        if not self.__is_initialized:
            self.first_start_initialize()
            return

        self.__main_window.show()

    def __connect(self):
        self.__db_config_controller.con_test_requested.connect(self.__db_con_test)
        self.__db_config_controller.con_params_obtained.connect(self.__db_con_created)
        self.__db_config_controller.initialization_cancelled.connect(self.__initialization_cancelled)
        self.__layer_dialogs_controller.layers_selected.connect(self.__layers_selected)
        self.__layer_dialogs_controller.columns_configured.connect(self.__columns_configured)
        self.__layer_dialogs_controller.layer_select_back_requested.connect(self.__back_to_db_config)
        self.__layer_dialogs_controller.column_setup_back_requested.connect(self.__back_to_layer_select)
        self.__layer_dialogs_controller.initialization_cancelled.connect(self.__initialization_cancelled)

    def __init_views(self):
        self.__main_window = MainWindow(
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
            self.__settings_service,
            self.__vehicle_service,
            self.__weather_service
        )
        self.__settings_controller.reconnect_requested.connect(self.__on_reconnect_requested)
        self.__settings_controller.graph_rebuild_requested.connect(self.__on_graph_rebuild_requested)
        self.__settings_controller.weather_settings_saved.connect(self.__apply_weather_settings)

        self.__main_window_controller = MainWindowController(
            model=self.__main_window_model,
            routing_service=self.__routing_service,
        )
        self.__main_window_controller.open_settings_requested.connect(
            self.__settings_controller.open_dialog_tab
        )
        self.__main_window_controller.map_layers_requested.connect(
            self.__load_map_layers
        )
        self.__main_window_controller.active_restriction_nodes_requested.connect(
            self.__provide_active_restriction_ids
        )

        self.__restriction_controller = RestrictionDialogController(
            self.__restriction_model,
            self.__restriction_service
        )
        self.__main_window_controller.open_restrictions_requested.connect(
            self.__restriction_controller.open_dialog
        )
        self.__main_window_controller.refresh_restrictions_requested.connect(
            self.__restriction_controller.refresh_restrictions
        )
        self.__main_window_controller.restriction_point_selected.connect(
            self.__restriction_controller.on_point_selected
        )
        self.__restriction_controller.select_point_on_map_requested.connect(
            self.__main_window_controller.on_map_selection_requested
        )
        self.__restriction_controller.restrictions_display_data_changed.connect(
            self.__main_window_controller.on_restriction_display_data_changed
        )

        self.__settings_controller.active_profile_changed.connect(
            self.__main_window_controller.update_active_profile
        )

        self.__settings_controller.select_distance_setting_saved.connect(
            self.__main_window_controller.set_point_select_distance
        )

    def __init_repositories(self):
        self.__vehicle_repo = VehicleProfileRepository()
        self.__layer_repo = LayerRepository(self.__db_connection)
        self.__graph_repo = RoadGraphRepository(self.__db_connection)
        self.__restriction_repo = RestrictionRepository(self.__db_connection)

    def __init_services(self):
        self.__vehicle_service = VehicleService(self.__vehicle_repo)
        self.__spatial_data_service = SpatialDataService(
            self.__layer_repo,
            self.__graph_repo,
        )
        weather_settings = self.__settings_service.load_weather_settings()
        self.__weather_service = WeatherService(
            api_url=weather_settings.get("api_url", ""),
            api_key=weather_settings.get("api_key", "")
        )
        self.__routing_service = RoutingService(self.__graph_repo, self.__weather_service)
        self.__routing_service.set_weather_settings(weather_settings)
        self.__restriction_service = RestrictionService(self.__restriction_repo)

    def __create_connection(self, host, port, username, password, database) -> DbConnection:
        return DbConnection(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
        )

    @pyqtSlot(str, str, str, str, str)
    def __db_con_test(self, host, port, username, password, database):
        try:
            if self.__db_config_controller is None:
                raise PluginError("Не задан DbInitController.")

            Logger.info("Идёт проверка соединения с базой данных...")
            self.__db_connection = self.__create_connection(
                host=host,
                port=port,
                username=username,
                password=password,
                database=database
            )
            schemas = self.__db_connection.get_schemas()
            self.__db_config_model.schemas = schemas

            if len(schemas) == 0:
                QMessageBox.warning(self.__layer_select_dialog, "Внимание",
                                 f"В заданной базе данных отсутствуют схемы!", QMessageBox.Ok)
        except Exception as e:
            self.__db_config_controller.connection_failed.emit(str(e))
        finally:
            Logger.info("Проверка соединения выполнена.")

    def __db_con_created(self):
        try:
            self.__db_connection.schema = self.__db_config_model.schema

            if self.__main_window_controller and self.__settings_controller:
                self.__main_window.close()
                self.__settings_dialog.close()

            self.__reset_init_selection()
            self.__init_repositories()
            self.__init_services()
            self.__layer_dialogs_controller.set_service(self.__spatial_data_service)
            self.__init_controllers()
            self.__init_views()

            self.__layer_select_dialog.open()
        except Exception as e:
            QMessageBox.critical(
                None, "Ошибка",
                f"Не удалось завершить инициализацию плагина:\n{e}",
                QMessageBox.Ok
            )
            Logger.error(f"Не удалось завершить инициализацию плагина: {e}")
            self.__initialization_failed()

    def __back_to_db_config(self):
        self.__db_config_dialog.open()

    def __layers_selected(self):
        self.__selected_layers = self.__layers_config_model.selected_layers
        self.__cols_config_dialog.open()

    def __back_to_layer_select(self):
        self.__layer_select_dialog.open()

    def __columns_configured(self):
        self.__column_mapping = self.__cols_config_model.mappings
        self.__configure_weather_location()
        self.__initialization_finished()

    def __configure_weather_location(self):
        if not self.__weather_service:
            return

        coords = self.__spatial_data_service.get_first_point_source_coordinates(
            list(self.__selected_layers),
            dict(self.__column_mapping),
        )
        if coords is None:
            return

        lon, lat = coords
        self.__weather_service.set_location(lon, lat)

    def __apply_weather_settings(self, settings: dict):
        if self.__weather_service:
            self.__weather_service.set_api_key(settings.get("api_key", ""))

        if self.__routing_service:
            self.__routing_service.set_weather_settings(settings)

    def __load_map_layers(self, selected_layers: list | None = None):
        layers = self.__spatial_data_service.get_spatial_layers()
        if selected_layers:
            layers.extend(self.__spatial_data_service.get_selected_spatial_layers(selected_layers))
        self.__main_window_controller.set_map_layers(layers)

    def __provide_active_restriction_ids(self, profile):
        node_ids = []
        temp_node_ids = self.__restriction_service.get_active_temp_restriction_node_ids()
        dim_node_ids = self.__restriction_service.get_active_dimension_restriction_node_ids(profile.height, profile.width, profile.weight)
        simple_node_ids = self.__restriction_service.get_active_simple_restriction_node_ids()

        node_ids.extend(temp_node_ids)
        node_ids.extend(dim_node_ids)
        node_ids.extend(simple_node_ids)

        self.__main_window_controller.set_active_restriction_node_ids(node_ids)

    def __initialization_finished(self):
        selected_layers = list(self.__selected_layers)
        column_mapping = dict(self.__column_mapping)

        Logger.info("Запускается процесс создания графа")
        try:
            def run_in_background(task: QgsTask):
                task.setProgress(0)
                self.__spatial_data_service.run_init_database(selected_layers, column_mapping)
                task.setProgress(50)
                self.__restriction_service.run_init_database()
                task.setProgress(100)
                return True

            def on_finished(exception, result=None):
                if exception:
                    QMessageBox.critical(iface.mainWindow(), "Ошибка",
                                         f"Не удалось инициализировать БД:\n{exception}", QMessageBox.Ok)
                    Logger.error(f"Не удалось инициализировать БД:\n{exception}")
                    if self.__is_reconnecting:
                        self.__reconnect_cancelled()
                    else:
                        self.__initialization_failed()
                    return
                self.__on_topology_build_finished()

            self.__build_task = QgsTask.fromFunction(
                "Инициализация базы данных",
                run_in_background,
                on_finished=on_finished,
            )
            QgsApplication.taskManager().addTask(self.__build_task)
        except Exception as e:
            QMessageBox.critical(iface.mainWindow(), "Ошибка",
                f"Не удалось построить граф:\n{e}\nПлагин завершает работу.", QMessageBox.Ok)
            Logger.error(f"Не удалось построить граф:\n{e}\nПлагин завершает работу.")
            self.crit_plugin_error.emit()

    def __on_topology_build_finished(self):
        Logger.info("Граф успешно создан!")
        if self.__settings_service and self.__db_connection:
            self.__settings_service.save_db_params(self.__db_connection)
        self.__finish_reconnect()
        self.__is_initialized = True
        self.plugin_initialized.emit()
        self.__initialize_map()
        Logger.info("Инициализация плагина завершена!")

    def __on_topology_rebuild_finished(self):
        self.__initialize_map()
        self.__settings_dialog.close()
        Logger.info("Граф перестроен!")

    def __initialization_cancelled(self):
        if self.__is_reconnecting:
            self.__reconnect_cancelled()
            Logger.warning("Пользователь отменил процесс инициализации")
            return

        self.__is_initialized = False
        if self.__main_window_controller:
            self.__main_window.close()
        self.__reset_initialization_state()
        self.plugin_init_cancelled.emit()

    def __initialization_failed(self):
        self.__is_initialized = False
        if self.__main_window:
            self.__main_window.close()
        if self.__settings_dialog:
            self.__settings_dialog.close()
        self.__reset_initialization_state()
        self.plugin_init_cancelled.emit()

    def __initialize_map(self):
        self.__main_window_controller.initialize_map(
            selected_layers=list(self.__selected_layers or [])
        )
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
                    Logger.error(f"Не удалось инициализировать БД:\n{exception}")
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
            Logger.error(f"Не удалось перестроить граф:\n{e}")

    def __on_reconnect_requested(self):
        self.__is_reconnecting = True
        self.__capture_reconnect_snapshot()
        try:
            self.__db_config_dialog.open()
        except Exception as e:
            QMessageBox.critical(None, "Ошибка",
                                 f"Во время переподключения произошла ошибка:\n{e}", QMessageBox.Ok)
            Logger.error(f"Во время переподключения произошла ошибка:\n{e}")
            self.__reconnect_cancelled()

    def __reconnect_cancelled(self):
        snapshot = self.__reconnect_snapshot
        if not snapshot:
            Logger.warning("Пользователь отменил переподключение к БД!")
            self.__finish_reconnect()
            return

        for dialog in (self.__db_config_dialog, self.__layer_select_dialog, self.__cols_config_dialog):
            if dialog and dialog.isVisible():
                dialog.hide()

        current_main_window = self.__main_window
        current_settings_dialog = self.__settings_dialog

        self.__db_connection = snapshot["db_connection"]
        self.__settings_service = snapshot["settings_service"]
        self.__spatial_data_service = snapshot["spatial_data_service"]
        self.__routing_service = snapshot["routing_service"]
        self.__restriction_service = snapshot["restriction_service"]
        self.__weather_service = snapshot["weather_service"]
        self.__vehicle_service = snapshot["vehicle_service"]
        self.__vehicle_repo = snapshot["vehicle_repo"]
        self.__layer_repo = snapshot["layer_repo"]
        self.__graph_repo = snapshot["graph_repo"]
        self.__restriction_repo = snapshot["restriction_repo"]
        self.__main_window_controller = snapshot["main_window_controller"]
        self.__settings_controller = snapshot["settings_controller"]
        self.__restriction_controller = snapshot["restriction_controller"]
        self.__main_window = snapshot["main_window"]
        self.__settings_dialog = snapshot["settings_dialog"]
        self.__restriction_dialog = snapshot["restriction_dialog"]
        self.__selected_layers = snapshot["selected_layers"]
        self.__column_mapping = snapshot["column_mapping"]
        self.__layers_config_model.selected_layers = copy.deepcopy(snapshot["layer_model_selection"])
        self.__cols_config_model.mappings = copy.deepcopy(snapshot["columns_mappings"])

        if current_main_window and current_main_window is not self.__main_window:
            current_main_window.close()
        if current_settings_dialog and current_settings_dialog is not self.__settings_dialog:
            current_settings_dialog.close()

        if self.__layer_dialogs_controller is not None:
            self.__layer_dialogs_controller.set_service(self.__spatial_data_service)
        if self.__settings_service and self.__db_connection:
            self.__settings_service.save_db_params(self.__db_connection)
        if self.__main_window:
            self.__main_window.show()

        self.__finish_reconnect()

    def __capture_reconnect_snapshot(self):
        if self.__reconnect_snapshot is not None:
            return
        self.__reconnect_snapshot = {
            "db_connection": self.__db_connection,
            "settings_service": self.__settings_service,
            "spatial_data_service": self.__spatial_data_service,
            "routing_service": self.__routing_service,
            "restriction_service": self.__restriction_service,
            "weather_service": self.__weather_service,
            "vehicle_service": self.__vehicle_service,
            "vehicle_repo": self.__vehicle_repo,
            "layer_repo": self.__layer_repo,
            "graph_repo": self.__graph_repo,
            "restriction_repo": self.__restriction_repo,
            "main_window_controller": self.__main_window_controller,
            "settings_controller": self.__settings_controller,
            "restriction_controller": self.__restriction_controller,
            "main_window": self.__main_window,
            "settings_dialog": self.__settings_dialog,
            "restriction_dialog": self.__restriction_dialog,
            "selected_layers": self.__selected_layers,
            "column_mapping": self.__column_mapping,
            "layer_model_selection": copy.deepcopy(self.__layers_config_model.selected_layers),
            "columns_mappings": copy.deepcopy(self.__cols_config_model.mappings),
        }

    def __finish_reconnect(self):
        self.__is_reconnecting = False
        self.__reconnect_snapshot = None
        Logger.info(f"Процесс переподключения к БД завершён")

    def __reset_init_selection(self):
        self.__layers_config_model.clear()
        self.__cols_config_model.clear()
        self.__selected_layers = []
        self.__column_mapping = {}

    def __reset_initialization_state(self):
        self.__db_config_model.clear()
        self.__reset_init_selection()
        self.__db_connection = None
        self.__spatial_data_service = None
        self.__layer_dialogs_controller.set_service(None)

    def __restore_init_dialogs_controllers(self):
        self.__db_config_controller: DbInitController = DbInitController(
            model=self.__db_config_model
        )
        self.__layer_dialogs_controller: LayerDialogsController = LayerDialogsController(
            layer_config_model=self.__layers_config_model,
            columns_config_model=self.__cols_config_model
        )
        self.__connect()

    def unload(self):
        if self.__main_window_controller is not None:
            self.__main_window_controller.on_clear_everything()
            Logger.info("Плагин выгружается")
