from dataclasses import dataclass


@dataclass
class RoutePointDto:
    id: int
    point_type: str
    order: int
    x: float
    y: float
    node_id: int | None = None
