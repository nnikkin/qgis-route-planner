import os
import qgis_route_planner.resources as resources

from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator, QTimer
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox

from qgis_route_planner.controllers.init_dialogs_controller import InitDialogsController
from qgis_route_planner.controllers.main_window_controller import MainWindowController
from qgis_route_planner.controllers.restriction_dialog_controller import RestrictionWindowController
from qgis_route_planner.controllers.settings_window_controller import SettingsWindowController
from qgis_route_planner.repositories.db_connection import DbConnection
from qgis_route_planner.repositories.graph_repository import RoadGraphRepository
from qgis_route_planner.repositories.layer_repository import LayerRepository
from qgis_route_planner.repositories.restriction_repository import RestrictionRepository
from qgis_route_planner.repositories.vehicle_repository import VehicleProfileRepository
from qgis_route_planner.services.database_service import DatabaseService
from qgis_route_planner.services.restriction_service import RestrictionService
from qgis_route_planner.services.routing_service import RoutingService
from qgis_route_planner.services.settings_service import SettingsService
from qgis_route_planner.views.select_layers_view import GeometryType


class QgisRoutePlanner:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = self.tr(u"&Поиск маршрутов")
        self.first_start = True

        self.__db_connection: DbConnection = None

        self.__settings_service: SettingsService = None
        self.__database_service: DatabaseService = None
        self.__routing_service: RoutingService = None
        self.__restriction_service: RestrictionService = None

        self.__vehicle_repo: VehicleProfileRepository = None
        self.__layer_repo: LayerRepository = None
        self.__graph_repo: RoadGraphRepository = None
        self.__restriction_repo: RestrictionRepository = None

        self.__main_controller: MainWindowController = None
        self.__init_dialogs_controller: InitDialogsController = None
        self.__settings_controller: SettingsWindowController = None
        self.__restriction_controller: RestrictionWindowController = None

        locale = QSettings().value("locale/userLocale")
        locale_path = os.path.join(self.plugin_dir, "i18n", f"QgisRoutePlanner_{locale}.qm")
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

    def tr(self, message):
        return QCoreApplication.translate("QgisRoutePlanner", message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None,
    ):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)
        if whats_this is not None:
            action.setWhatsThis(whats_this)
        if add_to_toolbar:
            self.iface.addToolBarIcon(action)
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initGui(self):
        icon_path = f"{self.plugin_dir}/png_resources/icon.png"
        self.add_action(
            icon_path,
            text=self.tr(u"Открыть модуль поиска маршрутов"),
            callback=self.run,
            parent=self.iface.mainWindow(),
        )
        self.first_start = True

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u"&Поиск маршрутов"), action)
            self.iface.removeToolBarIcon(action)

        if self.__main_controller is not None:
            self.__clear_everything()

    def __clear_everything(self):
        self.__main_controller.clear_all_points()
        self.__main_controller.clear_routes_list()
        self.__main_controller.clear_points_list()

    def __init_controllers(self):
        self.__settings_controller = SettingsWindowController(
            self.__settings_service
        )
        self.__settings_controller.reconnect_requested.connect(self.__reconnect_requested)
        self.__settings_controller.graph_rebuild_requested.connect(self.__on_graph_rebuild_requested)

        self.__main_controller = MainWindowController(
            self.__settings_controller,
            self.__database_service,
            self.__routing_service
        )
        # self.__restriction_controller = RestrictionController(self.__settings_dialog, self.__restriction_service)

    def __init_repositories(self):
        self.__vehicle_repo = VehicleProfileRepository(self.__db_connection)
        self.__layer_repo = LayerRepository(self.__db_connection)
        self.__graph_repo = RoadGraphRepository(self.__db_connection, self.__layer_repo)
        #self.__restriction_repo = RestrictionRepository(self.__db_connection)

    def __init_services(self):
        self.__settings_service = SettingsService(self.__vehicle_repo)
        self.__database_service = DatabaseService(self.__layer_repo, self.__graph_repo, self.__vehicle_repo)
        self.__routing_service = RoutingService(self.__graph_repo)
        #self.__restriction_service = RestrictionService(self.__restriction_repo)

    def run(self):
        if self.first_start:
            self.__init_dialogs_controller = InitDialogsController(self.__database_service)
            self.__init_dialogs_controller.db_connection_test.connect(
                self.__on_db_con_test
            )
            self.__init_dialogs_controller.db_connection_created.connect(
                self.__on_db_con_created
            )
            self.__init_dialogs_controller.initialization_finished.connect(
                self.__on_initialization_finished
            )
            self.__init_dialogs_controller.init_cancelled.connect(
                self.__on_initialization_cancelled
            )
            self.__init_dialogs_controller.start_init_process()
            return
        else:
            self.__main_controller.open_main_window()

    def __on_db_con_test(self, db_connection: DbConnection):
        self.__db_connection = db_connection
        temp_layer_repo = LayerRepository(self.__db_connection)
        temp_graph_repo = RoadGraphRepository(self.__db_connection, temp_layer_repo)
        temp_vehicle_repo = VehicleProfileRepository(self.__db_connection)
        temp_db_service = DatabaseService(temp_layer_repo, temp_graph_repo, temp_vehicle_repo)
        temp_settings_service = SettingsService(temp_vehicle_repo)

        self.__settings_controller = SettingsWindowController(temp_settings_service)

        self.__init_dialogs_controller.set_db_service(temp_db_service)
        self.__init_dialogs_controller.fill_schema_combobox()

    def __on_db_con_created(self, db_connection: DbConnection):
        self.__db_connection = db_connection

        if self.__main_controller and self.__settings_controller:
            self.__main_controller.close_main_window()
            QTimer.singleShot(0, self.__settings_controller.close_settings_window)

        self.__init_repositories()
        self.__init_services()
        self.__settings_service.save_db_params(self.__db_connection)
        self.__init_controllers()

    def __on_initialization_finished(self, selected_layers: list[tuple[str, GeometryType]], column_mapping: dict):
        self.first_start = False

        self.__selected_layers = selected_layers
        self.__column_mapping = column_mapping
        self.__database_service.run_init_database(self.__selected_layers, self.__column_mapping)
        self.__main_controller.open_main_window()
        self.__main_controller.initialize_map()

    def __on_initialization_cancelled(self):
        if self.__main_controller:
            self.__main_controller.close_main_window()

        self.first_start = True
        self.__init_dialogs_controller = None

    def __on_graph_rebuild_requested(self):
        try:
            self.__main_controller.close_main_window()
            self.__graph_repo.create_topology()
            self.__main_controller.open_main_window()
            self.__main_controller.initialize_map()
            self.__settings_controller.close_settings_window()
        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось перестроить граф:\n{e}", QMessageBox.Ok)

    def __on_reconnect_cancelled(self):
        pass

    def __reconnect_requested(self, init_ctrl: InitDialogsController):
        self.__init_dialogs_controller = init_ctrl

        init_ctrl.db_connection_test.connect(self.__on_db_con_test)
        init_ctrl.db_connection_created.connect(self.__on_db_con_created)
        init_ctrl.initialization_finished.connect(self.__on_initialization_finished)
        init_ctrl.init_cancelled.connect(self.__on_reconnect_cancelled)