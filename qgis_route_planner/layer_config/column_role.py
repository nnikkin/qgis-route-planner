from enum import Enum

class ColumnRole(Enum):
    PRIMARY_KEY = "Первичный ключ"
    GEOMETRY = "Геометрия (GEOMETRY)"
    HIGHWAY = "Дорожная сеть (HIGHWAY)"
    LANES_FORWARD = "Количество полос вперёд (LANES:FORWARD)"
    LANES_BACKWARD = "Количество полос назад (LANES:BACKWARD)"
    MAX_HEIGHT = "Макс. высота (MAX_HEIGHT)"
    MAX_WIDTH = "Макс. ширина (MAX_WIDTH)"
    MAX_WEIGHT = "Макс. вес (MAX_WEIGHT)"
    MAX_SPEED = "Макс. скорость (MAX_SPEED)"
    ONEWAY = "Одностороннее движение (ONEWAY)"
    BRIDGE = "Мосты (BRIDGE)"
    NAME = "Название (NAME/NAME_RU)"
    ADDRESS = "Адрес (ADDRESS)"
    LOCATION = "Расположение трубопровода (LOCATION)"
    OTHER = "Другие теги (OTHER_TAGS)"

    @classmethod
    def from_value(cls, value: str):
        for item in cls:
            if item.value == value:
                return item
        raise ValueError(f"Неизвестный тип поля: {value}")