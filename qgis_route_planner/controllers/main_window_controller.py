from __future__ import annotations

from ..data.models.main_window_model import MainWindowModel
from ..data.route import SelectedPointCollection, PointType
from ..data.vehicle import VehicleProfile
from ..services import SpatialDataService, RoutingService
from .settings_window_controller import SettingsWindowController

from qgis.PyQt.QtCore import QObject, pyqtSlot, pyqtSignal
from qgis.core import QgsPointXY


class MainWindowController(QObject):
    """Контроллер главного окна"""

    show_point_context_menu_requested = pyqtSignal(QgsPointXY, int)
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
        self._model: MainWindowModel = model
        self._settings_controller: SettingsWindowController = settings_controller
        self._db_service: SpatialDataService = db_service
        self._routing_service: RoutingService = routing_service
        self._current_route: SelectedPointCollection = SelectedPointCollection()

    def initialize_map(self, schema: str = "routing"):
        try:
            layers = self._db_service.get_spatial_layers(schema=schema)
            if not layers:
                print(f"В схеме '{schema}' не обнаружены таблицы с геоданными!")
                return
            return layers
        except Exception as e:
            print(f"Не удалось получить слои: {e}")
            return []

    @pyqtSlot(QgsPointXY)
    def on_map_point_selected(self, point: QgsPointXY):
        snapped = self._routing_service.snap_point_to_road(point)
        if not snapped:
            self._model.status_message = "error:snap"
            return

        snapped_point, node_id = snapped
        self.show_point_context_menu_requested.emit(snapped_point, node_id)

    @pyqtSlot(QgsPointXY, PointType, int)
    def on_add_route_point(self, qgs_point_xy: QgsPointXY, point_type: PointType, node_id: int):
        if not self._model.active_profile:
            self._model.status_message = "error:no_profile"
            return

        if node_id is None:
            node_id = self._routing_service.find_nearest_node(qgs_point_xy)

        if node_id is None:
            self._model.status_message = "error:no_node"
            return

        self._current_route.add_point(qgs_point_xy, point_type, node_id)
        route_point = self._current_route.get_point(self._current_route.next_point_id - 1)

        # Обновляем модель
        self._model.points = list(self._current_route.points)
        self.point_marker_add_requested.emit(route_point)

        self._try_build_routes()

    @pyqtSlot()
    def on_clear_everything(self):
        self._current_route.clear()
        self._model.clear()
        self.map_cleared.emit()

    @pyqtSlot(int)
    def on_route_selected(self, index: int):
        self._model.active_route_index = index

    @pyqtSlot(int)
    def on_save_route(self, route_index: int):
        routes = self._model.routes
        if route_index < 0 or route_index >= len(routes):
            return
        self._save_route_to_file(routes[route_index])

    def _save_route_to_file(self, route: list[dict]):
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
    def _try_build_routes(self):
        if not self._current_route.has_required_points():
            self._model.routes = []
            self.routes_display_requested.emit([])
            return

        point_ids = self._current_route.get_point_ids()
        start_node_id = point_ids[0]
        end_node_id = point_ids[-1]
        waypoint_ids = point_ids[1:-1]

        routes = self._routing_service.calculate_routes(
            start_node_id, end_node_id,
            self._model.active_profile, waypoint_ids
        )

        if not routes:
            self._model.status_message = "error:no_routes"
            self._model.routes = []
            self.routes_display_requested.emit([])
            return

        self._model.routes = routes
        self._model.active_tab = 1
        self.routes_display_requested.emit(routes)