from dataclasses import dataclass

from qgis.core import QgsPointXY

from qgis_route_planner.models.geometry_types import GeometryType
from qgis_route_planner.models.route.point_type import PointType


@dataclass
class RouteEdge:
    edge_id: int
    geom: str
    cost: float
    agg_cost: float
    seq: int | None = None