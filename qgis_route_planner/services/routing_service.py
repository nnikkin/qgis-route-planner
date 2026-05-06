from qgis.core import QgsPointXY

from qgis.PyQt.QtWidgets import QMessageBox

from qgis_route_planner.models.route.selected_point_collection import SelectedPointCollection
from qgis_route_planner.repositories.graph_repository import RoadGraphRepository


class RoutingService:
    """Сервис маршрутизации"""
    def __init__(self, graph_repo: RoadGraphRepository | None):
        self.__graph_repo: RoadGraphRepository = graph_repo
        self.__current_route: SelectedPointCollection = None

    def set_graph_repository(self, graph_repo: RoadGraphRepository | None):
        self.__graph_repo = graph_repo

    def is_point_on_road_network(self, point: QgsPointXY) -> bool:
        """Проверяет, находится ли точка на дорожной сети"""
        if not self.__graph_repo:
            return False
        return self.__graph_repo.is_point_on_road_network(point.x(), point.y())

    def find_nearest_node(self, point: QgsPointXY) -> int | None:
        """Находит ближайший узел графа к точке"""
        if not self.__graph_repo:
            return None
        result = self.__graph_repo.find_nearest_node(point.x(), point.y())
        if result:
            return result[0]  # Возвращаем только node_id
        return None

    def snap_point_to_road(self, point: QgsPointXY) -> tuple[QgsPointXY, int] | None:
        """Привязывает точку к ближайшему ребру и возвращает точку и ID узла этого ребра."""
        if not self.__graph_repo:
            return None

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

        if candidate_nodes:
            candidate_nodes.sort(key=lambda item: item[1])
            return snapped_point, candidate_nodes[0][0]

        return None

    def calculate_route(self, start_node_id: int, end_node_id: int, waypoints_ids: list[int] = None) -> list[dict] | None:
        """Вычисляет маршрут между двумя узлами"""
        try:
            if not self.__graph_repo:
                QMessageBox.critical(
                    None,
                    "",
                    "Репозиторий графа не инициализирован!",
                    QMessageBox.Ok
                )
                return None

            route = self.__graph_repo.get_route(start_node_id, end_node_id, waypoints_ids)
            self.__current_route = route
            return route
        except Exception as e:
            print(f"Error calculating route: {e}")
            return None

    def get_route_info(self, route: list[dict]) -> dict:
        """Получает информацию о маршруте (длина, время)"""
        if not route:
            return {
                'distance_km': 0,
                'time_hours': 0,
                'time_minutes': 0,
                'segments': 0
            }
        total_distance = sum(edge['cost'] for edge in route)
        total_time = total_distance / 60

        return {
            'distance_km': total_distance / 1000,
            'time_hours': total_time / 60,
            'time_minutes': total_time,
            'segments': len(route)
        }

    def clear_route(self):
        """Очищает текущий маршрут"""
        self.__current_route = None
