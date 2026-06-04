from dataclasses import dataclass

@dataclass
class ProfileDto:
    id: int | None
    name: str
    type: str
    height_m: float
    width_m: float
    depth_m: float
    weight_t: float