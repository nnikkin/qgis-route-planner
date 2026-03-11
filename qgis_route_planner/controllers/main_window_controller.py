from __future__ import annotations

from ..data.models.main_window_model import MainWindowModel
from ..data.route import SelectedPointCollection, PointType
from ..services import SpatialDataService, RoutingService
from .settings_window_controller import SettingsWindowController

from qgis.PyQt.QtCore import QObject, pyqtSlot, pyqtSignal
from qgis.core import QgsPointXY


class MainWindowController(QObject):
    """Контроллер главного окна"""

    layers_obtained = pyqtSignal(list)
    show_point_context_menu_requested = pyqtSignal(object, int)
    routes_display_requested = pyqtSignal(list)
    map_cleared = pyqtSignal()
    point_marker_add_requested = pyqtSignal(object)
    point_marker_remove_requested = pyqtSignal(int)
    point_marker_update_requested = pyqtSignal(int)
    open_settings_requested = pyqtSignal(int)

    def __init__(
            self,
            model: MainWindowModel,
            settings_controller: SettingsWindowController,
            db_service: SpatialDataService,
            routing_service: RoutingService,
    ):
        super().__init__()

        self.__model: MainWindowModel = model
        self.__settings_controller: SettingsWindowController = settings_controller

        self.__db_service: SpatialDataService = db_service
        self.__routing_service: RoutingService = routing_service

        self.__current_route: SelectedPointCollection = SelectedPointCollection()

    def open_settings_dialog(self, tab_index: int = 0):
        self.__settings_controller.open_dialog_tab(tab_index)

    def initialize_map(self, schema: str = "routing"):
        try:
            layers = self.__db_service.get_spatial_layers(schema=schema)
            if not layers:
                raise BaseException(f"В схеме '{schema}' не обнаружены таблицы с геоданными!")
            self.layers_obtained.emit(layers)
        except Exception as e:
            raise BaseException(f"Не удалось получить слои: {e}")

    @pyqtSlot(QgsPointXY)
    def on_map_point_selected(self, point: QgsPointXY):
        snapped = self.__routing_service.snap_point_to_road(point)
        if not snapped:
            self.__model.status_message = "error:snap"
            return

        snapped_point, node_id = snapped
        self.show_point_context_menu_requested.emit(snapped_point, node_id)

    @pyqtSlot(QgsPointXY, PointType, int)
    def on_add_route_point(self, qgs_point_xy: QgsPointXY, point_type: PointType, node_id: int):
        if not self.__model.active_profile:
            self.__model.status_message = "error:no_profile"
            return

        if node_id is None:
            node_id = self.__routing_service.find_nearest_node(qgs_point_xy)

        if node_id is None:
            self.__model.status_message = "error:no_node"
            return

        self.__current_route.add_point(qgs_point_xy, point_type, node_id)
        route_point = self.__current_route.get_point(self.__current_route.next_point_id - 1)

        self.__model.points = list(self.__current_route.points)
        self.point_marker_add_requested.emit(route_point)

        self.__try_build_routes()

    @pyqtSlot()
    def on_clear_everything(self):
        self.__current_route.clear()
        self.__model.clear()
        self.map_cleared.emit()

    @pyqtSlot(int)
    def on_route_selected(self, index: int):
        self.__model.active_route_index = index

    @pyqtSlot(int)
    def on_save_route(self, route_index: int):
        routes = self.__model.routes
        if route_index < 0 or route_index >= len(routes):
            return
        self.__save_route_to_file(routes[route_index])

    def __save_route_to_file(self, route: list[dict]):
        from qgis.PyQt.QtWidgets import QFileDialog
        file_url, _ = QFileDialog.getSaveFileUrl(
            None,
            "Выберите место для сохранения файла",
            "",
            "HTML-файл (*.html)",
        )
        if file_url and not file_url.isEmpty():
            # TODO: реализовать экспорт
            pass

    # Внутренние методы
    def __try_build_routes(self):
        if not self.__current_route.has_required_points():
            self.__model.routes = []
            self.routes_display_requested.emit([])
            return

        point_ids = self.__current_route.get_point_ids()
        start_node_id = point_ids[0]
        end_node_id = point_ids[-1]
        waypoint_ids = point_ids[1:-1]

        routes = self.__routing_service.calculate_routes(
            start_node_id, end_node_id,
            self.__model.active_profile, waypoint_ids
        )

        if not routes:
            self.__model.status_message = "error:no_routes"
            self.__model.routes = []
            self.routes_display_requested.emit([])
            return

        self.__model.routes = routes
        self.__model.active_tab = 1
        self.routes_display_requested.emit(routes)