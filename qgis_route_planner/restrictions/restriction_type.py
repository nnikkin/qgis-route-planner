from enum import Enum

class RestrictionType(Enum):
    SIMPLE = 1
    DIMENSION = 2
    TEMPORARY = 3

    @classmethod
    def get_as_str(self, restriction_type: int) -> str:
        match restriction_type:
            case RestrictionType.SIMPLE.value:
                return "Простое"
            case RestrictionType.DIMENSION.value:
                return "По габаритам ТС"
            case RestrictionType.TEMPORARY:
                return "По времени"