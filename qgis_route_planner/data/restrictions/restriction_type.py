from enum import Enum

class RestrictionType(Enum):
    TEMPORARY = "По времени (аварии, работы...)"
    DIMENSION = "По габаритам ТС"
    SIMPLE = "Простое"


    @classmethod
    def from_value(cls, value: str):
        for item in cls:
            if item.value == value:
                return item
        raise ValueError(f"Неизвестный тип ограничения: {value}")