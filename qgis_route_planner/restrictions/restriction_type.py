from enum import Enum

class RestrictionType(Enum):
    SIMPLE = "Простое"
    TEMPORARY = "По времени"
    DIMENSION = "По габаритам ТС"

    @classmethod
    def from_value(cls, value: str):
        for item in cls:
            if item.value == value:
                return item
        raise ValueError(f"Неизвестный тип ограничения: {value}")