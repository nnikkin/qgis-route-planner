from dataclasses import dataclass


@dataclass
class ActiveProfileDto:
    id: int | None
    name: str