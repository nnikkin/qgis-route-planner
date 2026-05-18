from dataclasses import dataclass


@dataclass
class RouteEdge:
    edge_id: int
    geom: str
    cost: float
    agg_cost: float
    seq: int | None = None