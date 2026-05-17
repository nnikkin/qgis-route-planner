from dataclasses import dataclass

from qgis_route_planner.vehicle import VehicleType


@dataclass
class VehicleProfile:
    id: int | None = None
    name: str = ""
    type: VehicleType = None
    height: float = 0.01
    width: float = 0.01
    weight: float = 0.01
    depth: float = 0.01
