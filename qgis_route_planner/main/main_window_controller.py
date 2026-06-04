from __future__ import annotations
from typing import TYPE_CHECKING

from qgis_route_planner.logger import Logger
from qgis_route_planner.exceptions import DataImportError

if TYPE_CHECKING:
    from main_window_model import MainWindowModel
    from qgis_route_planner.restrictions.restriction_model import RestrictionModel
    from qgis_route_planner.restrictions.restriction_dialog_controller import RestrictionDialogController
    from qgis_route_planner.restrictions.restriction_service import RestrictionService
    from qgis_route_planner.settings.settings_dialog_controller import SettingsDialogController
    from qgis_route_planner.setup.spatial_data_service import TableService
    from qgis_route_planner.routing.routing_service import RoutingService

from qgis_route_planner.routing.selected_point_collection import SelectedPointCollection
from qgis_route_planner.routing.point_type import PointType
from qgis_route_planner.main.route_export_service import RouteExportService

from qgis.PyQt.QtCore import pyqtSlot, pyqtSignal
from qgis.core import QgsPointXY

class MainWindowController:
    """ Контроллер главного окна """

    layers_obtained = pyqtSignal(list)
    show_point_context_menu_requested = pyqtSignal(object, object)
    routes_display_requested = pyqtSignal(list)
    map_cleared = pyqtSignal()
    point_marker_add_requested = pyqtSignal(object)
    point_marker_remove_requested = pyqtSignal(int)
    point_marker_update_requested = pyqtSignal(int)

    select_point_on_map_requested = pyqtSignal(bool)
    restriction_point_added = pyqtSignal(int, float, float)

    restrictions_display_requested = pyqtSignal(list)
    restrictions_display_cleared = pyqtSignal()

    show_error = pyqtSignal(str)
    show_warning = pyqtSignal(str)
    show_info = pyqtSignal(str)

    def __init__(
            self,
            model: MainWindowModel,
            restriction_model: RestrictionModel,
            settings_controller: SettingsDialogController,
            restr_controller: RestrictionDialogController,
            data_service: TableService,
            routing_service: RoutingService,
            restriction_service: RestrictionService,
    ):
        super().__init__()

        self.__model: MainWindowModel = model
        self.__restriction_model: RestrictionModel = restriction_model
        self.__settings_controller: SettingsDialogController = settings_controller
        self.__restr_controller: RestrictionDialogController = restr_controller
        self.__restr_controller.select_point_on_map_requested.connect(
            self.__on_map_selection_requested
        )
        self.__restriction_model.restrictions_changed.connect(
            self.__on_restrictions_changed
        )
        self.__restriction_model.current_restriction_id_changed.connect(
            self.__on_current_restriction_changed
        )

        self.__data_service: TableService = data_service
        self.__routing_service: RoutingService = routing_service
        self.__restriction_service: RestrictionService = restriction_service

        self.__current_route: SelectedPointCollection = SelectedPointCollection()

        self.__restriction_points: dict[int, tuple[float, float]] = {}
        self.__map_canvas = None
        self.__route_export_service = RouteExportService()

    def set_map_canvas(self, canvas):
        self.__map_canvas = canvas

    def open_settings_dialog(self, tab_index: int = 0):
        self.__settings_controller.open_dialog_tab(tab_index)

    def open_restriction_dialog(self):
        self.__restr_controller.open_dialog()

    @pyqtSlot(bool)
    def set_restrictions_visible(self, visible: bool):
        self.__model.restrictions_visible = visible
        if visible:
            self.__restr_controller.refresh_restrictions()
            self.__update_visible_restrictions()
            Logger.info("Ограничения отображаются на карте")
        else:
            Logger.info("Ограничения скрыты с карты")
            self.restrictions_display_cleared.emit()

    def initialize_map(self, schema: str = "routing", selected_layers: list | None = None):
        layers = self.__data_service.get_spatial_layers(schema=schema)
        if selected_layers:
            layers.extend(self.__data_service.get_selected_spatial_layers(selected_layers))
        if not layers:
            raise DataImportError(f"В схеме '{schema}' не обнаружены таблицы с геоданными")
        self.layers_obtained.emit(layers)

    @pyqtSlot(QgsPointXY)
    def on_map_point_selected(self, point: QgsPointXY):
        self.__routing_service.set_point_select_distance(self.__settings_controller.get_select_point_distance())
        snapped = self.__routing_service.snap_point_to_road(point)
        if not snapped:
            self.__model.status_message = "error:snap"
            return

        snapped_point, snap_info = snapped

        self.show_point_context_menu_requested.emit(snapped_point, snap_info)

    @pyqtSlot(QgsPointXY, PointType, object)
    def on_add_route_point(self, qgs_point_xy: QgsPointXY, point_type: PointType, snap_info):
        if not self.__model.active_profile:
            self.__model.status_message = "error:no_profile"
            return

        if not isinstance(snap_info, dict):
            snap_info = {"node_id": snap_info}

        node_id = snap_info.get("node_id")
        edge_id = snap_info.get("edge_id")
        fraction = snap_info.get("fraction")

        if node_id is None and edge_id is None:
            self.__model.status_message = "error:no_node"
            return

        self.__current_route.add_point(
            qgs_point_xy, point_type, node_id,
            edge_id=edge_id, fraction=fraction
        )
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
        try:
            saved_path = self.__route_export_service.save_route(routes[route_index], self.__map_canvas)
            if saved_path:
                self.__model.status_message = f"Маршрут сохранён: {saved_path}"
        except Exception as e:
            self.__model.status_message = f"Ошибка сохранения маршрута: {e}"

    def __try_build_routes(self):
        if not self.__current_route.has_required_points():
            self.__model.routes = []
            self.routes_display_requested.emit([])
            return

        point_ids = self.__current_route.get_point_ids()
        if not point_ids:
            return

        start_node_id = point_ids[0]
        end_node_id = point_ids[-1]
        waypoint_ids = point_ids[1:-1]
        restriction_node_ids = self.__restriction_service.get_active_restriction_node_ids(
            self.__model.active_profile
        )

        p1 = f"Запрошено построение маршрутов из точки {start_node_id} в точку {end_node_id}"
        p2 = f" с промежуточными точками {waypoint_ids}" if waypoint_ids else ""

        Logger.info(p1 + p2)

        routes = self.__routing_service.calculate_routes(
            start_node_id, end_node_id,
            self.__model.active_profile, waypoint_ids, restriction_node_ids, self.__current_route.points
        )

        if not routes:
            Logger.info("Маршруты не найдены")
            self.__model.status_message = "error:no_routes"
            self.__model.routes = []
            self.routes_display_requested.emit([])
            return

        Logger.info(f"Найдено маршрутов: {len(routes)}")
        self.__model.routes = routes
        self.__model.active_tab = 1
        self.routes_display_requested.emit(routes)

    @pyqtSlot(object)
    def update_active_profile(self, profile):
        """ Обновляет активный профиль в модели главного окна """
        self.__model.active_profile = profile

    @pyqtSlot(bool)
    def __on_map_selection_requested(self, active: bool = True):
        """ Запрос диалога ограничений """
        self.__model.restriction_select_mode = active

    def on_add_restriction_point(self, point: QgsPointXY, node_id: int):
        """ Добавить точку ограничения """
        self.__restriction_points[node_id] = (point.x(), point.y())
        self.restriction_point_added.emit(node_id, point.x(), point.y())
        self.__restr_controller.on_point_selected(point, node_id)
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
        self.__routing_service.set_point_select_distance(self.__settings_controller.get_select_point_distance())
        return self.__routing_service.snap_point_to_road(point)

    def __on_restrictions_changed(self, _restrictions: list):
        self.__update_visible_restrictions()

    def __on_current_restriction_changed(self, _restriction_id: int | None):
        self.__update_visible_restrictions()

    def __update_visible_restrictions(self):
        if not self.__model.restrictions_visible:
            return

        selected_id = self.__restriction_model.current_restriction_id
        restriction_points = []

        for restriction in self.__restriction_model.restrictions:
            if restriction.node_id is None:
                continue
            coords = self.__routing_service.get_node_coordinates(restriction.node_id)
            if not coords:
                continue
            restriction_points.append({
                "id": restriction.id,
                "node_id": restriction.node_id,
                "x": coords[0],
                "y": coords[1],
                "selected": restriction.id == selected_id,
            })

        self.restrictions_display_requested.emit(restriction_points)
