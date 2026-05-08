from __future__ import annotations
from typing import TYPE_CHECKING

from qgis_route_planner.logger import Logger
from qgis_route_planner.exceptions import DataImportError

if TYPE_CHECKING:
    from .main_window_model import MainWindowModel
    from qgis_route_planner.routing.routing_service import RoutingService

from qgis_route_planner.routing.selected_point_collection import SelectedPointCollection
from qgis_route_planner.routing.point_type import PointType
from qgis_route_planner.main.active_profile_dto import ActiveProfileDto
from qgis_route_planner.main.point_dto import RoutePointDto
from qgis_route_planner.main.route_export_service import RouteExportService

from qgis.PyQt.QtCore import pyqtSlot, pyqtSignal, QObject
from qgis.core import QgsPointXY

class MainWindowController(QObject):
    """ Контроллер главного окна """

    layers_obtained = pyqtSignal(list)
    show_point_context_menu_requested = pyqtSignal(object, object)
    routes_display_requested = pyqtSignal(list)
    map_cleared = pyqtSignal()
    points_reordered = pyqtSignal(list)
    point_marker_add_requested = pyqtSignal(object)
    point_marker_remove_requested = pyqtSignal(int)
    point_marker_update_requested = pyqtSignal(int)
    open_settings_requested = pyqtSignal(int)
    map_layers_requested = pyqtSignal(object)
    select_point_on_map_requested = pyqtSignal(bool)
    open_restrictions_requested = pyqtSignal()
    refresh_restrictions_requested = pyqtSignal()
    active_restriction_nodes_requested = pyqtSignal(object)
    restriction_point_selected = pyqtSignal(object, int)
    restriction_point_added = pyqtSignal(int, float, float)
    restrict_points_display_requested = pyqtSignal(list)
    restrict_points_display_cleared = pyqtSignal()
    show_error = pyqtSignal(str)
    show_warning = pyqtSignal(str)
    show_info = pyqtSignal(str)

    def __init__(
            self,
            model: MainWindowModel,
            routing_service: RoutingService,
    ):
        super().__init__()

        self.__model: MainWindowModel = model

        self.__routing_service: RoutingService = routing_service

        self.__current_route: SelectedPointCollection = SelectedPointCollection()
        self.__active_profile: ActiveProfileDto | None = None
        self.__active_restriction_node_ids: list[int] = []
        self.__restriction_display_data: list[dict] = []

        self.__restriction_points: dict[int, tuple[float, float]] = {}
        self.__map_canvas = None
        self.__route_export_service = RouteExportService()

    def set_map_canvas(self, canvas):
        self.__map_canvas = canvas

    def set_selected_point(self, point_id: int | None):
        self.__model.selected_point_id = point_id

    def open_settings_dialog(self, tab_index: int = 0):
        self.open_settings_requested.emit(tab_index)

    def open_restriction_dialog(self):
        self.open_restrictions_requested.emit()

    @pyqtSlot(bool)
    def set_restrictions_visible(self, visible: bool):
        self.__model.restrictions_visible = visible
        if visible:
            self.refresh_restrictions_requested.emit()
            self.__update_visible_restrictions()
            Logger.info("Ограничения отображаются на карте")
        else:
            Logger.info("Ограничения скрыты с карты")
            self.restrict_points_display_cleared.emit()

    def initialize_map(self, schema: str = "routing", selected_layers: list | None = None):
        self.map_layers_requested.emit(selected_layers)

    @pyqtSlot(list)
    def set_map_layers(self, layers: list):
        if not layers:
            raise DataImportError("В выбранной схеме не обнаружены таблицы с геоданными")
        self.layers_obtained.emit(layers)

    @pyqtSlot(float)
    def set_point_select_distance(self, distance: float):
        self.__model.point_select_distance = distance
        self.__routing_service.set_point_select_distance(distance)

    @pyqtSlot(QgsPointXY)
    def on_map_point_selected(self, point: QgsPointXY):
        self.__routing_service.set_point_select_distance(self.__model.point_select_distance)
        snapped = self.__routing_service.snap_point_to_road(point)
        if not snapped:
            self.__model.statusbar_message = "error:snap"
            return

        snapped_point, snap_info = snapped

        self.show_point_context_menu_requested.emit(snapped_point, snap_info)

    @pyqtSlot(QgsPointXY, PointType, object)
    def on_add_route_point(self, qgs_point_xy: QgsPointXY, point_type: PointType, snap_info):
        if not self.__active_profile:
            self.__model.statusbar_message = "error:no_profile"
            return

        if not isinstance(snap_info, dict):
            snap_info = {"node_id": snap_info}

        node_id = snap_info.get("node_id")
        edge_id = snap_info.get("edge_id")
        fraction = snap_info.get("fraction")

        if node_id is None and edge_id is None:
            self.__model.statusbar_message = "error:no_node"
            return

        idx = self.__current_route.add_point(
            qgs_point_xy, point_type, node_id,
            edge_id=edge_id, fraction=fraction
        )
        route_point = self.__current_route.get_point(idx - 1)

        self.__model.points = [
            self.__route_point_to_dto(point)
            for point in self.__current_route.points
        ]
        self.point_marker_add_requested.emit(route_point)

        self.__try_build_routes()

    @pyqtSlot()
    def on_clear_everything(self):
        self.__current_route.clear()
        self.__model.clear()
        self.map_cleared.emit()

    @pyqtSlot()
    def on_move_point_up(self):
        selected_id = self.__get_selected_point_id()
        if selected_id is None:
            return
        if self.__current_route.move_up(selected_id):
            self.__sync_points_and_rebuild()

    @pyqtSlot()
    def on_move_point_down(self):
        selected_id = self.__get_selected_point_id()
        if selected_id is None:
            return
        if self.__current_route.move_down(selected_id):
            self.__sync_points_and_rebuild()

    @pyqtSlot()
    def on_delete_point(self):
        selected_id = self.__get_selected_point_id()
        if selected_id is None:
            return
        if self.__current_route.remove_point(selected_id):
            self.point_marker_remove_requested.emit(selected_id)
            for p in self.__current_route.points:
                self.point_marker_update_requested.emit(p.id)
            self.__sync_points_and_rebuild()

    def __get_selected_point_id(self) -> int | None:
        return self.__model.selected_point_id

    def __sync_points_and_rebuild(self):
        """ Обновить модель и пересчитать маршрут """
        self.__model.points = [
            self.__route_point_to_dto(p)
            for p in self.__current_route.points
        ]

        for p in self.__current_route.points:
            self.point_marker_update_requested.emit(p.id)
        self.__try_build_routes()

    @pyqtSlot(int)
    def on_route_selected(self, index: int):
        self.__model.active_route_index = index

    @pyqtSlot(int)
    def on_save_route(self, route_index: int):
        routes = self.__model.routes
        if route_index < 0 or route_index >= len(routes):
            return
        try:
            saved_path = self.__route_export_service.save_route(routes[route_index], self.__map_canvas)
            if saved_path:
                self.__model.statusbar_message = f"Маршрут сохранён: {saved_path}"
        except Exception as e:
            self.__model.statusbar_message = f"Ошибка сохранения маршрута: {e}"

    def __try_build_routes(self):
        if not self.__current_route.has_required_points():
            self.__model.routes = []
            self.routes_display_requested.emit([])
            return

        point_ids = self.__current_route.get_routing_node_ids()
        if not point_ids:
            return

        start_node_id = point_ids[0]
        end_node_id = point_ids[-1]
        waypoint_ids = point_ids[1:-1]
        self.active_restriction_nodes_requested.emit(self.__active_profile)
        restriction_node_ids = list(self.__active_restriction_node_ids)

        p1 = f"Запрошено построение маршрутов из точки {start_node_id} в точку {end_node_id}"
        p2 = f" с промежуточными точками {waypoint_ids}" if waypoint_ids else ""

        Logger.info(p1 + p2)

        found_routes = self.__routing_service.calculate_routes(
            start_node_id, end_node_id,
            self.__active_profile, waypoint_ids, restriction_node_ids, self.__current_route.points
        )

        if not found_routes:
            Logger.info("Маршруты не найдены")
            self.__model.statusbar_message = "error:no_routes"
            self.__model.routes = []
            self.routes_display_requested.emit([])
            return

        Logger.info(f"Найдено маршрутов: {len(found_routes)}")
        self.__model.routes = found_routes
        self.__model.active_tab = 1
        self.routes_display_requested.emit(found_routes)

    @pyqtSlot(object)
    def update_active_profile(self, profile):
        """ Обновляет активный профиль в модели главного окна """
        self.__active_profile = profile
        self.__model.active_profile = self.__profile_to_dto(profile)

    @pyqtSlot(list)
    def set_active_restriction_node_ids(self, node_ids: list[int]):
        self.__active_restriction_node_ids = node_ids

    @pyqtSlot(bool)
    def on_map_selection_requested(self, active: bool = True):
        """ Запрос диалога ограничений """
        self.__model.restriction_select_mode = active

    def on_add_restriction_point(self, point: QgsPointXY, node_id: int):
        """ Добавить точку ограничения """
        self.__restriction_points[node_id] = (point.x(), point.y())
        self.restriction_point_added.emit(node_id, point.x(), point.y())
        self.restriction_point_selected.emit(point, node_id)
        self.__model.restriction_select_mode = False

    def cancel_add_restriction_point(self):
        self.__restriction_points.clear()
        self.__model.restriction_select_mode = False

    def clear_restriction_points(self):
        """ Очистить точки ограничений """
        self.__restriction_points.clear()

    def get_restriction_nodes(self) -> list[int]:
        """ Получить список узлов с ограничениями """
        return list(self.__restriction_points.keys())

    def snap_point(self, point: QgsPointXY):
        self.__routing_service.set_point_select_distance(self.__model.point_select_distance)
        return self.__routing_service.snap_point_to_road(point)

    @pyqtSlot(list)
    def on_restriction_display_data_changed(self, restrictions: list[dict]):
        self.__restriction_display_data = restrictions
        self.__update_visible_restrictions()

    def __update_visible_restrictions(self):
        if not self.__model.restrictions_visible:
            return

        restriction_points = []

        for restriction in self.__restriction_display_data:
            node_id = restriction.get("node_id")
            if node_id is None:
                continue
            coords = self.__routing_service.get_node_coordinates(node_id)
            if not coords:
                continue
            restriction_points.append({
                "id": restriction.get("id"),
                "node_id": node_id,
                "x": coords[0],
                "y": coords[1],
                "selected": restriction.get("selected", False),
            })

        self.restrict_points_display_requested.emit(restriction_points)

    @staticmethod
    def __route_point_to_dto(route_point) -> RoutePointDto:
        return RoutePointDto(
            id=route_point.id,
            point_type=route_point.point_type,
            order=route_point.order,
            x=route_point.qgs_point_xy.x(),
            y=route_point.qgs_point_xy.y(),
            node_id=route_point.node_id,
        )

    @staticmethod
    def __profile_to_dto(profile) -> ActiveProfileDto | None:
        if profile is None:
            return None
        return ActiveProfileDto(
            id=getattr(profile, "id", None),
            name=getattr(profile, "name", ""),
        )
