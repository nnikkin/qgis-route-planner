from qgis.PyQt.QtCore import pyqtSignal, QObject
from ...utils import FormMode
from ..route.restriction_record import RestrictionRecord
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


class RestrictionModel(QObject):
    restrictions_changed = pyqtSignal(list)
    active_restriction_id_changed = pyqtSignal(object)
    current_restriction_id_changed = pyqtSignal(object)
    editing_mode_changed = pyqtSignal(FormMode)
    current_restriction_data_changed = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.__restrictions: list[RestrictionRecord] = []
        self.__active_restriction_id: int = None
        self.__current_restriction_id: int = None
        self.__editing_mode: FormMode = FormMode.EMPTY
        self.__current_restriction_data: RestrictionRecord = None

    def get_restrictions(self) -> list[RestrictionRecord]:
        return self.__restrictions.copy()

    def get_active_restriction_id(self) -> int | None:
        return self.__active_restriction_id

    def get_current_restriction_id(self) -> int | None:
        return self.__current_restriction_id

    def get_editing_mode(self) -> FormMode:
        return self.__editing_mode

    def get_current_restriction_data(self) -> RestrictionRecord | None:
        return self.__current_restriction_data

    def set_restrictions(self, restrictions: list[RestrictionRecord]):
        self.__restrictions = restrictions
        self.restrictions_changed.emit(self.get_restrictions())

    def set_active_restriction_id(self, restriction_id: int | None):
        if self.__active_restriction_id != restriction_id:
            self.__active_restriction_id = restriction_id
            self.active_restriction_id_changed.emit(restriction_id)

    def set_current_restriction_id(self, restriction_id: int | None):
        if self.__current_restriction_id != restriction_id:
            self.__current_restriction_id = restriction_id
            self.current_restriction_id_changed.emit(restriction_id)

    def set_editing_mode(self, mode: FormMode):
        if self.__editing_mode != mode:
            self.__editing_mode = mode
            self.editing_mode_changed.emit(mode)

    def set_current_restriction_data(self, data: RestrictionRecord | None):
        self.__current_restriction_data = data
        self.current_restriction_data_changed.emit(data)

    def find_restriction_by_id(self, restriction_id: int) -> RestrictionRecord | None:
        for r in self.__restrictions:
            if r.id == restriction_id:
                return r
        return None