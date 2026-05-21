from enum import Enum

class RestrictionType(Enum):
    SIMPLE = 1
    DIMENSION = 2
    TEMPORARY = 3

    @classmethod
    def get_as_str(cls, restriction_type) -> str:
        if isinstance(restriction_type, cls):
            restriction_type = restriction_type.value
        try:
            restriction_type = int(restriction_type)
        except (TypeError, ValueError):
            return "Неизвестно"

        names = {
            cls.SIMPLE.value: "Простое",
            cls.DIMENSION.value: "По габаритам ТС",
            cls.TEMPORARY.value: "По времени",
        }
        return names.get(restriction_type, "Неизвестно")