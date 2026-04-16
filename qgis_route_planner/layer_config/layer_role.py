from enum import Enum

class LayerRole(Enum):
    ROADS = "Слой дорог"
    POINTS = "Слой точек"
    PARKING = "Слой парковок"
    PIPING = "Слой трубопроводов"
    FOR_CONTEXT = "Контекстный слой"

    @classmethod
    def from_value(cls, value: str):
        for item in cls:
            if item.value == value:
                return item
        raise ValueError(f"Неизвестная роль для слоя: {value}")