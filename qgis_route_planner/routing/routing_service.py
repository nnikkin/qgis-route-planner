from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qgis_route_planner.vehicle import VehicleProfile

from qgis.core import QgsPointXY
from qgis.PyQt.QtWidgets import QMessageBox

from qgis_route_planner.exceptions import WeatherServiceError, NodeNotFoundError

from selected_point_collection import SelectedPointCollection
from graph_provider import GraphProvider
from weather_service import WeatherService


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
        self.__summer_avg_speed_kmh: float = 60.0
        self.__winter_avg_speed_kmh: float = 45.0
        self.__max_distance: float = 0

    def set_weather_settings(self, settings: dict | None):
        settings = settings or {}
        self.__fallback_season = settings.get("fallback_season", self.__fallback_season)
        self.__summer_avg_speed_kmh = self.__positive_float(
            settings.get("summer_avg_speed_kmh"),
            self.__summer_avg_speed_kmh,
        )
        self.__winter_avg_speed_kmh = self.__positive_float(
            settings.get("winter_avg_speed_kmh"),
            self.__winter_avg_speed_kmh,
        )

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
        for node_key in ("source", "target"):
            node_id = edge_info.get(node_key)
            if node_id is None:
                continue
            coords = self.__graph_provider.get_node_coordinates(node_id)
            if coords:
                nearest_node_id = int(node_id)
                break

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
            self.calculate_weather()
        except WeatherServiceError as err:
            raise err

        if self.__weather_service and self.__weather_service.has_api_key():
            route_speed_kmh = self.__weather_service.get_season_speed(
                self.__summer_avg_speed_kmh,
                self.__winter_avg_speed_kmh,
                self.__fallback_season,
            )
        else:
            route_speed_kmh = (
                self.__summer_avg_speed_kmh
                if self.__fallback_season == "summer"
                else self.__winter_avg_speed_kmh
            )

        try:
            routes = self.__graph_provider.get_routes(
                start_node_id, end_node_id, profile,
                waypoints_ids, route_points, restriction_nodes,
                route_speed_kmh=route_speed_kmh
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
