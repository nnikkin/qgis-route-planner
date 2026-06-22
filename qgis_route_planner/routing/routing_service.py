from __future__ import annotations

from qgis.core import QgsPointXY
from qgis.PyQt.QtWidgets import QMessageBox

from qgis_route_planner.exceptions import WeatherServiceError, NodeNotFoundError

from .selected_point_collection import SelectedPointCollection
from .graph_provider import GraphProvider
from .weather_service import WeatherService
from ..vehicle import VehicleProfile


class RoutingService:
    """ Сервис маршрутизации """

    def __init__(
            self,
            graph_provider: GraphProvider | None,
            weather_service: WeatherService | None = None,
    ):
        self.__graph_provider: GraphProvider = graph_provider
        self.__weather_service: WeatherService | None = weather_service
        self.__current_route: SelectedPointCollection = None
        self.__current_weather: dict | None = None
        self.__fallback_season: str = "summer"
        self.__summer_factor = 1.0
        self.__winter_factor = 0.75
        self.__max_distance: float = 0

    def set_weather_settings(self, settings: dict | None):
        settings = settings or {}
        self.__fallback_season = settings.get("fallback_season", self.__fallback_season)

    def set_point_select_distance(self, distance: float):
        self.__max_distance = distance

    def calculate_weather(self) -> dict | None:
        if not self.__weather_service:
            return None
        self.__current_weather = self.__weather_service.calculate_weather()
        return self.__current_weather

    def get_node_coordinates(self, node_id: int) -> tuple[float, float] | None:
        """ Возвращает координаты узла графа  """
        if not self.__graph_provider:
            return None
        return self.__graph_provider.get_node_coordinates(node_id)

    def snap_point_to_road(self, point: QgsPointXY) -> tuple[QgsPointXY, dict] | None:
        """ Привязывает точку к ближайшему ребру и возвращает точку и параметры привязки """
        if not self.__graph_provider:
            return None

        edge_info = self.__graph_provider.find_nearest_edge(point.x(), point.y(), self.__max_distance)
        if not edge_info:
            return None

        snapped_point = QgsPointXY(float(edge_info["snapped_x"]), float(edge_info["snapped_y"]))
        nearest_node_id = None
        nearest_node_distance = None
        for node_key in ("source", "target"):
            node_id = edge_info.get(node_key)
            if node_id is None:
                continue
            coords = self.__graph_provider.get_node_coordinates(node_id)
            if coords:
                distance = (coords[0] - snapped_point.x()) ** 2 + (coords[1] - snapped_point.y()) ** 2
                if nearest_node_distance is None or distance < nearest_node_distance:
                    nearest_node_id = int(node_id)
                    nearest_node_distance = distance

        snap_info = {
            "node_id": nearest_node_id,
            "edge_id": edge_info["edge_id"],
            "fraction": edge_info["fraction"],
        }
        return snapped_point, snap_info

    def calculate_routes(
            self,
            start_node_id: int,
            end_node_id: int,
            profile: VehicleProfile,
            waypoints_ids: list[int] = None,
            restriction_nodes: list[int] = None,
            route_points: list = None
    ) -> list[list[dict]] | None:

        if not self.__graph_provider:
            QMessageBox.critical(
                None,
                "",
                "Репозиторий графа не инициализирован!",
                QMessageBox.Ok
            )
            return None

        try:
            weather_data = self.calculate_weather()
        except WeatherServiceError as err:
            raise err

        if self.__weather_service and self.__weather_service.has_api_key():
            season_factor = self.__weather_service.get_season_factor(
                summer_factor=self.__summer_factor,
                winter_factor=self.__winter_factor,
                fallback=self.__fallback_season,
                data=weather_data,
            )
        else:
            season_factor = (
                self.__summer_factor
                if self.__fallback_season == "summer"
                else self.__winter_factor
            )

        try:
            routes = self.__graph_provider.get_routes(
                profile,
                start_node_id,
                end_node_id,
                waypoints_ids,
                route_points,
                restriction_nodes,
                season_factor=season_factor,
            )

            if routes:
                self.__current_route = routes[0]
                return routes
            else:
                return None
        except NodeNotFoundError as e:
            raise e

    def __positive_float(self, value, default: float) -> float:
        try:
            number = float(value)
            return number if number > 0 else default
        except (TypeError, ValueError):
            return default
