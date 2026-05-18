from enum import Enum


class GeometryType(Enum):
    LINESTRING = "Линия"
    POINT = "Точка"
    POLYGON = "Полигон"
    MULTILINESTRING = "Мультилиния"
    MULTIPOLYGON = "Мультиполигон"

    @classmethod
    def from_value(cls, value: str):
        for item in cls:
            if item.value == value:
                return item
        raise ValueError(f"Неизвестный тип геометрии: {value}")