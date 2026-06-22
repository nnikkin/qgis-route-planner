from typing import Protocol


class GraphProvider(Protocol):
    def get_node_coordinates(self, node_id: int):
        pass

    def find_nearest_edge(self, x: float, y: float, max_distance: float):
        pass

    def get_routes(
        self,
        profile,
        start_id: int,
        end_id: int,
        waypoint_ids: list[int] = None,
        route_points: list = None,
        restriction_nodes: list[int] = None,
        season_factor: float = 1,
        routes_n: int = 3
    ):
        pass