from enum import Enum

class RestrictionType(Enum):
    DIMENSION = 1
    TEMPORARY = 2

    @classmethod
    def get_as_str(cls, restriction_type) -> str:
        if isinstance(restriction_type, cls):
            restriction_type = restriction_type.value
        try:
            restriction_type = int(restriction_type)
        except (TypeError, ValueError):
            return "Неизвестно"

        names = {
            cls.DIMENSION.value: "По габаритам ТС",
            cls.TEMPORARY.value: "По времени",
        }
        return names.get(restriction_type, "Неизвестно")