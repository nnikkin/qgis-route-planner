from qgis.PyQt.QtWidgets import QMessageBox

from . import (
    InitDialogsController,
    MainWindowController,
    RestrictionWindowController,
    SettingsWindowController,
)
from ..data.models import DbConfigModel, LayerConfigModel, ColumnsConfigModel, SettingsModel

from ..repositories import (
    RoadGraphRepository,
    LayerRepository,
    RestrictionRepository,
    VehicleProfileRepository,
    DbConnection,
)

from ..services import (
    SpatialDataService,
    RestrictionService,
    RoutingService,
    SettingsService,
)

from ..views import PluginMainWindow, ConnectionConfigDialog, SettingsDialog, LayersSelectDialog, LayerColumnsDialog


class PluginController:
    """Контроллер плагина"""
    def __init__(self):
        self.__db_config_model: DbConfigModel = DbConfigModel()
        self.__layers_config_model: LayerConfigModel = LayerConfigModel()
        self.__cols_config_model: ColumnsConfigModel = ColumnsConfigModel()
        self.__settings_model: SettingsModel = SettingsModel()

        self.__main_window_controller: MainWindowController = None
        self.__settings_controller: SettingsWindowController = None
        self.__restriction_controller: RestrictionWindowController = None
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
        self.__main_window: PluginMainWindow = None
        self.__restriction_dialog = None
        self.__settings_dialog: SettingsDialog = None

        self.__db_connection: DbConnection = None

        self.__settings_service: SettingsService = None
        self.__spatial_data_service: SpatialDataService = None
        self.__routing_service: RoutingService = None
        self.__restriction_service: RestrictionService = None

        self.__vehicle_repo: VehicleProfileRepository = None
        self.__layer_repo: LayerRepository = None
        self.__graph_repo: RoadGraphRepository = None
        self.__restriction_repo: RestrictionRepository = None

        self.__connect_slots_signals()

    def first_start_initialize(self):
        self.__db_config_dialog.open()

    def open_main_window(self):
        self.__main_window.show()


    def __connect_slots_signals(self):
        self.__init_dialogs_controller.con_test_requested.connect(
            self.__db_con_test
        )
        self.__init_dialogs_controller.con_params_obtained.connect(
            self.__db_con_created
        )
        self.__init_dialogs_controller.layers_selected.connect(
            self.__layers_selected
        )
        self.__init_dialogs_controller.columns_configured.connect(
            self.__columns_configured
        )
        self.__init_dialogs_controller.init_cancelled.connect(
            self.__initialization_cancelled
        )

    def __init_views(self):
        self.__main_window = PluginMainWindow()
        self.__settings_dialog = SettingsDialog(
            model=self.__settings_model
        )
        #self.__restriction_dialog =

    def __init_controllers(self):
        self.__settings_controller = SettingsWindowController(
            self.__settings_model,
            self.__settings_dialog,
            self.__settings_service
        )
        self.__settings_controller.reconnect_requested.connect(self.__reconnect_requested)
        self.__settings_controller.graph_rebuild_requested.connect(self.__on_graph_rebuild_requested)

        self.__main_window_controller = MainWindowController(
            self.__settings_controller,
            self.__spatial_data_service,
            self.__routing_service,
            self.__main_window,
        )
        # self.__restriction_controller = RestrictionController(self.__settings_dialog, self.__restriction_service)

    def __init_repositories(self):
        self.__vehicle_repo = VehicleProfileRepository(self.__db_connection)
        self.__layer_repo = LayerRepository(self.__db_connection)
        self.__graph_repo = RoadGraphRepository(self.__db_connection, self.__layer_repo)
        #self.__restriction_repo = RestrictionRepository(self.__db_connection)

    def __init_services(self):
        self.__settings_service = SettingsService(self.__vehicle_repo)
        self.__spatial_data_service = SpatialDataService(self.__layer_repo, self.__graph_repo, self.__vehicle_repo)
        self.__routing_service = RoutingService(self.__graph_repo)
        #self.__restriction_service = RestrictionService(self.__restriction_repo)


    def __db_con_test(self):
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

    def __db_con_created(self):
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

        self.__init_views()
        self.__init_repositories()
        self.__init_services()
        self.__init_controllers()

        self.__settings_service.save_db_params(self.__db_connection)

        self.__layer_select_dialog.open()

    def __layers_selected(self):
        self.__selected_layers = self.__layers_config_model.selected_layers
        self.__cols_config_dialog.open()

    def __columns_configured(self):
        self.__column_mapping = self.__cols_config_model.mappings
        self.__initialization_finished()

    def __initialization_finished(self ):
        self.first_start = False

        self.__spatial_data_service.run_init_database(self.__selected_layers, self.__column_mapping)

        self.__main_window_controller.open_main_window()
        self.__main_window_controller.initialize_map()

    def __initialization_cancelled(self):
        if self.__main_window_controller:
            self.__main_window.close()

        self.first_start = True
        self.__init_dialogs_controller = None

    def __on_graph_rebuild_requested(self):
        try:
            self.__main_window.close()
            self.__graph_repo.create_topology()
            self.__main_window_controller.open_main_window()
            self.__main_window_controller.initialize_map()
            self.__settings_dialog.close()
        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось перестроить граф:\n{e}", QMessageBox.Ok)

    def __reconnect_requested(self):
        self.__init_dialogs_controller.con_test_requested.connect(
            self.__db_con_test
        )
        self.__init_dialogs_controller.con_params_obtained.connect(
            self.__db_con_created
        )
        self.__init_dialogs_controller.columns_configured.connect(
            self.__columns_configured
        )
        self.__init_dialogs_controller.init_cancelled.connect(
            self.__reconnect_cancelled
        )

    def __reconnect_cancelled(self):
        pass

    def unload(self):
        if self.__main_window_controller is not None:
            self.__main_window_controller.clear_everything()
