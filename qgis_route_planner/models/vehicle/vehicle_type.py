from enum import Enum

class VehicleType(Enum):
    CAR = dict(ru="Легковой", name="car")
    TRUCK = dict(ru="Грузовой", name="truck")

    @classmethod
    def from_value(cls, value: str):
        for item in cls:
            if item.value == value:
                return item
        raise ValueError(f"Неизвестный тип ТС: {value}")