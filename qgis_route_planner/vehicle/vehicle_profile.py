from dataclasses import dataclass

from qgis_route_planner.vehicle import VehicleType


@dataclass
class VehicleProfile:
    id: int | None = None
    name: str = ""
    type: VehicleType = None
    height_m: float = 0.0
    width_m: float = 0.0
    weight_t: float = 0.0
    depth_m: float = 0.0
