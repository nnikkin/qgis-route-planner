from dataclasses import dataclass


@dataclass
class ActiveProfileDto:
    id: int | None
    name: str
    height: float
    width: float
    weight: float
    type: str