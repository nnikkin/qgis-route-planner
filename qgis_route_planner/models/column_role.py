from enum import Enum

class ColumnRole(Enum):
    PRIMARY_KEY = "Первичный ключ"
    GEOMETRY = "Геометрия (GEOMETRY)"
    HIGHWAY = "Дорожная сеть (HIGHWAY)"
    WATERWAY = "Водные пути (WATERWAY)"
    AERIALWAY = "Канатные дороги (AERIALWAY)"
    RAILWAY = "Железные дороги (RAILWAY)"
    MAN_MADE = "Искусственные сооружения (MAN_MADE)"
    BARRIER = "Преграды (BARRIER)"
    NAME = "Название (NAME)"
    ADDRESS = "Адрес (ADDRESS)"
    IS_IN = "Местоположение (IS_IN)"
    Z_ORDER = "Порядок отрисовки (Z_ORDER)"
    REF = "Справочный номер (REF)"
    OTHER = "Другие теги (OTHER_TAGS)"

    @classmethod
    def from_value(cls, value: str):
        for item in cls:
            if item.value == value:
                return item
        raise ValueError(f"Неизвестный тип поля: {value}")