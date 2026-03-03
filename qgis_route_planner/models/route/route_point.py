from dataclasses import dataclass

from qgis.core import QgsPointXY
from qgis_route_planner.models.route.point_type import PointType


@dataclass
class RoutePoint:
    id: int
    qgs_point_xy: QgsPointXY
    point_type: PointType
    order: int
    node_id: int = None
    address: str = ""

    def to_dict(self):
        return {
            'id': self.id,
            'x': self.qgs_point_xy.x(),
            'y': self.qgs_point_xy.y(),
            'type': self.point_type.value,
            'order': self.order,
            'node_id': self.node_id,
            'address': self.address
        }