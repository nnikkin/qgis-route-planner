from __future__ import annotations

from qgis.core import QgsPointXY

from qgis.PyQt.QtWidgets import QMessageBox

from ..data.route import SelectedPointCollection
from ..data.vehicle import VehicleProfile
from ..repositories import RoadGraphRepository
from .weather_service import WeatherService


class RoutingService:
    """ Сервис маршрутизации """

    def __init__(
            self,
            graph_repo: RoadGraphRepository | None,
            weather_service: WeatherService | None = None,
    ):
        self.__graph_repo: RoadGraphRepository = graph_repo
        self.__weather_service: WeatherService | None = weather_service
        self.__current_route: SelectedPointCollection = None
        self.__current_weather: dict | None = None
        self.__fallback_season: str = "summer"
        self.__summer_avg_speed_kmh: float = 60.0
        self.__winter_avg_speed_kmh: float = 45.0

    def set_graph_repository(self, graph_repo: RoadGraphRepository | None):
        self.__graph_repo = graph_repo

    def set_weather_service(self, weather_service: WeatherService | None):
        self.__weather_service = weather_service

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

    def set_weather_location(self, lon: float, lat: float):
        if self.__weather_service:
            self.__weather_service.set_location(lon, lat)

    def calculate_weather(self) -> dict | None:
        if not self.__weather_service:
            return None
        self.__current_weather = self.__weather_service.calculate_weather()
        return self.__current_weather

    def is_point_on_road_network(self, point: QgsPointXY) -> bool:
        """ Проверяет, находится ли точка на дорожной сети """
        if not self.__graph_repo:
            return False
        return self.__graph_repo.is_point_on_road_network(point.x(), point.y())

    def find_nearest_node(self, point: QgsPointXY) -> int | None:
        """ Находит ближайший узел графа к точке """
        if not self.__graph_repo:
            return None
        result = self.__graph_repo.find_nearest_node(point.x(), point.y())
        if result:
            return result[0]  # Возвращаем только node_id
        return None

    def get_node_coordinates(self, node_id: int) -> tuple[float, float] | None:
        """ Возвращает координаты узла графа  """
        if not self.__graph_repo:
            return None
        return self.__graph_repo.get_node_coordinates(node_id)

    def snap_point_to_road(self, point: QgsPointXY) -> tuple[QgsPointXY, dict] | None:
        """ Привязывает точку к ближайшему ребру и возвращает точку и параметры привязки """
        if not self.__graph_repo:
            return None

        nearest_node = self.__graph_repo.find_nearest_node(point.x(), point.y(), max_distance_m=50.0)
        if nearest_node:
            node_id = int(nearest_node[0])
            node_coords = self.__graph_repo.get_node_coordinates(node_id)
            if node_coords:
                return QgsPointXY(float(node_coords[0]), float(node_coords[1])), {"node_id": node_id}

        edge_info = self.__graph_repo.find_nearest_edge(point.x(), point.y())
        if not edge_info:
            return None

        snapped_point = QgsPointXY(float(edge_info["snapped_x"]), float(edge_info["snapped_y"]))
        candidate_nodes: list[tuple[int, float]] = []

        for node_id in (edge_info.get("source"), edge_info.get("target")):
            if node_id is None:
                continue
            coords = self.__graph_repo.get_node_coordinates(node_id)
            if coords:
                dx = snapped_point.x() - coords[0]
                dy = snapped_point.y() - coords[1]
                candidate_nodes.append((int(node_id), dx * dx + dy * dy))

        nearest_node_id = None
        if candidate_nodes:
            candidate_nodes.sort(key=lambda item: item[1])
            nearest_node_id = candidate_nodes[0][0]

        if nearest_node_id is None:
            return None

        node_coords = self.__graph_repo.get_node_coordinates(nearest_node_id)
        if node_coords:
            snapped_point = QgsPointXY(float(node_coords[0]), float(node_coords[1]))

        snap_info = {
            "node_id": nearest_node_id,
        }
        return snapped_point, snap_info

    def calculate_routes(
            self,
            start_node_id: int,
            end_node_id: int,
            profile: VehicleProfile,
            waypoints_ids: list[int] = None,
            restriction_nodes: list[int] = None,
            route_points: list | None = None,
    ) -> list[list[dict]] | None:
        try:
            if not self.__graph_repo:
                QMessageBox.critical(
                    None,
                    "",
                    "Репозиторий графа не инициализирован!",
                    QMessageBox.Ok
                )
                return None

            self.calculate_weather()

            routes = self.__graph_repo.get_routes(start_node_id, end_node_id, profile, waypoints_ids, restriction_nodes)

            if routes:
                self.__current_route = routes[0]
                return routes
            else:
                return None
        except Exception as e:
            return None

    def get_route_info(self, route: list[dict]) -> dict:
        """ Получает информацию о маршруте (длина, время) """
        if not route:
            return {
                'distance_km': 0,
                'time_hours': 0,
                'time_minutes': 0,
                'segments': 0
            }
        total_distance = sum(edge['length_m'] for edge in route)
        total_time = sum(edge['cost'] for edge in route)

        return {
            'distance_km': total_distance / 1000,
            'time_minutes': total_time / 60,
            'segments': len(route)
        }

    def clear_route(self):
        """ Очищает текущий маршрут """
        self.__current_route = None

    def __fallback_speed_kmh(self) -> float:
        if self.__fallback_season == "winter":
            return self.__winter_avg_speed_kmh
        return self.__summer_avg_speed_kmh

    def __positive_float(self, value, default: float) -> float:
        try:
            number = float(value)
            return number if number > 0 else default
        except (TypeError, ValueError):
            return default
