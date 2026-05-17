from typing import Protocol


class GraphProvider(Protocol):
    def get_node_coordinates(self, node_id: int):
        pass

    def find_nearest_edge(self, x: float, y: float, max_distance: float):
        pass

    def get_routes(self, start_node_id: int, end_node_id: int, profile,
                   waypoints_ids: list[int], route_points: list, restriction_nodes: list[int], route_speed_kmh: float):
        pass