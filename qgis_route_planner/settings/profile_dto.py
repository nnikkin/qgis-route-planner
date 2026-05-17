from dataclasses import dataclass

@dataclass
class ProfileDto:
    id: int | None
    name: str
    type: str
    height: float
    width: float
    depth: float
    weight: float