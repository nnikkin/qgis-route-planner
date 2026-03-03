from dataclasses import dataclass


@dataclass
class VehicleProfile:
    id: int | None = None
    name: str = ""
    type: str = None
    height_m: float = 0.0
    width_m: float = 0.0
    weight_t: float = 0.0
    depth_m: float = 0.0
    max_speed_kmh: float = 0.0
