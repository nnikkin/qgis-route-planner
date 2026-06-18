from enum import Enum

class VehicleType(Enum):
    CAR = "Легковой"
    TRUCK = "Грузовой"

    @classmethod
    def from_value(cls, value: str):
        for item in cls:
            if item.value == value or item.name.lower() == value.lower():
                return item
        raise ValueError(f"Неизвестный тип VehicleType: {value}")