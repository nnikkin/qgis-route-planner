from enum import Enum

class ColumnRole(Enum):
    PRIMARY_KEY = "Первичный ключ"
    GEOMETRY = "Геометрия (GEOMETRY)"
    HIGHWAY = "Дорожная сеть (HIGHWAY)"
    MAX_HEIGHT = "Макс. высота (MAX_HEIGHT)"
    MAX_SPEED = "Макс. скорость (MAX_SPEED)"
    MAX_WIDTH = "Макс. ширина (MAX_WIDTH)"
    NAME = "Название (NAME)"
    ADDRESS = "Адрес (ADDRESS)"
    OTHER = "Другие теги (OTHER_TAGS)"

    @classmethod
    def from_value(cls, value: str):
        for item in cls:
            if item.value == value:
                return item
        raise ValueError(f"Неизвестный тип поля: {value}")