from qgis.PyQt.QtCore import pyqtSignal, QObject
from ...utils import FormMode
from ..route.restriction_record import RestrictionRecord
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


class RestrictionModel(QObject):
    restriction_type_changed = pyqtSignal(object)
    name_changed = pyqtSignal(str)
    comment_changed = pyqtSignal(str)
    point_changed = pyqtSignal(object)
    valid_from_changed = pyqtSignal(object)
    valid_to_changed = pyqtSignal(object)
    max_height_changed = pyqtSignal(float)
    max_weight_changed = pyqtSignal(float)
    max_width_changed = pyqtSignal(float)
    restrictions_changed = pyqtSignal(list)
    active_restriction_id_changed = pyqtSignal(object)
    current_restriction_id_changed = pyqtSignal(object)
    current_restriction_data_changed = pyqtSignal(object)
    editing_mode_changed = pyqtSignal(FormMode)
    any_field_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.__name = ""
        self.__comment = ""
        self.__restriction_type = RestrictionType.SIMPLE
        self.__point = None

        self.__valid_from = None
        self.__valid_to = None
        self.__max_height = 0.0
        self.__max_width = 0.0
        self.__max_weight = 0.0

        self.__restrictions: list[RestrictionRecord] = []
        self.__active_restriction_id: int = None
        self.__current_restriction_id: int = None
        self.__editing_mode: FormMode = FormMode.EMPTY
        self.__current_restriction_data: RestrictionRecord = None

        for signal in (
                self.restriction_type_changed,
                self.name_changed,
                self.comment_changed,
                self.point_changed,
                self.valid_from_changed,
                self.valid_to_changed,
                self.max_height_changed,
                self.max_width_changed,
                self.max_weight_changed,
        ):
            signal.connect(self.__on_any_changed)

    @property
    def restriction_type(self) -> RestrictionType:
        return self.__restriction_type

    @restriction_type.setter
    def restriction_type(self, value: RestrictionType):
        self.__restriction_type = value or RestrictionType.SIMPLE
        self.restriction_type_changed.emit(self.__restriction_type)

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value
        self.name_changed.emit(value)

    @property
    def comment(self):
        return self.__comment

    @comment.setter
    def comment(self, value):
        self.__comment = value
        self.comment_changed.emit(value)

    @property
    def point(self):
        return self.__point

    @point.setter
    def point(self, value):
        self.__point = value
        self.point_changed.emit(value)


    @property
    def valid_from(self):
        return self.__valid_from

    @valid_from.setter
    def valid_from(self, value):
        self.__valid_from = value
        self.valid_from_changed.emit(value)

    @property
    def valid_to(self):
        return self.__valid_to

    @valid_to.setter
    def valid_to(self, value):
        self.__valid_to = value
        self.valid_to_changed.emit(value)

    @property
    def max_height(self):
        return self.__max_height

    @max_height.setter
    def max_height(self, value):
        self.__max_height = value
        self.max_height_changed.emit(value)

    @property
    def max_width(self):
        return self.__max_width

    @max_width.setter
    def max_width(self, value):
        self.__max_width = value
        self.max_width_changed.emit(value)

    @property
    def max_weight(self):
        return self.__max_weight

    @max_weight.setter
    def max_weight(self, value):
        self.__max_weight = value
        self.max_weight_changed.emit(value)

    @property
    def restrictions(self) -> list[RestrictionRecord]:
        return self.__restrictions.copy()

    @restrictions.setter
    def restrictions(self, restrictions: list[RestrictionRecord]):
        self.__restrictions = restrictions
        self.restrictions_changed.emit(self.restrictions)

    @property
    def active_restriction_id(self) -> int | None:
        return self.__active_restriction_id

    @active_restriction_id.setter
    def active_restriction_id(self, restriction_id: int | None):
        if self.__active_restriction_id != restriction_id:
            self.__active_restriction_id = restriction_id
            self.active_restriction_id_changed.emit(restriction_id)

    @property
    def current_restriction_id(self) -> int | None:
        return self.__current_restriction_id

    @current_restriction_id.setter
    def current_restriction_id(self, restriction_id: int | None):
        if self.__current_restriction_id != restriction_id:
            self.__current_restriction_id = restriction_id
            self.current_restriction_id_changed.emit(restriction_id)

    @property
    def editing_mode(self) -> FormMode:
        return self.__editing_mode

    @editing_mode.setter
    def editing_mode(self, mode: FormMode):
        if self.__editing_mode != mode:
            self.__editing_mode = mode
            self.editing_mode_changed.emit(mode)

    @property
    def current_restriction_data(self) -> RestrictionRecord | None:
        return self.__current_restriction_data

    @current_restriction_data.setter
    def current_restriction_data(self, data: RestrictionRecord | None):
        self.__current_restriction_data = data
        self.current_restriction_data_changed.emit(data)

    def find_restriction_by_id(self, restriction_id: int) -> RestrictionRecord | None:
        for r in self.__restrictions:
            if r.id == restriction_id:
                return r
        return None

    def get_node_ids(self) -> list[int]:
        node_ids = []
        node_id = self.__node_id_from_point_data(self.__point)
        if node_id is not None:
            node_ids.append(node_id)
        return node_ids

    def clear_form(self):
        self.name = ""
        self.comment = ""
        self.restriction_type = RestrictionType.SIMPLE
        self.point = None
        self.valid_from = None
        self.valid_to = None
        self.max_height = 0.0
        self.max_width = 0.0
        self.max_weight = 0.0

    def load_record(self, record: RestrictionRecord):
        self.current_restriction_data = record
        self.name = record.name
        self.comment = record.comment
        self.restriction_type = RestrictionRecord.id_to_type(record.restriction_type_id)
        self.point = (None, record.node_id) if record.node_id is not None else None
        self.max_height = 0.0
        self.max_width = 0.0
        self.max_weight = 0.0
        self.valid_from = None
        self.valid_to = None

        if self.restriction_type == RestrictionType.DIMENSION:
            values = record.dimension_values()
            self.max_height = values["height"]
            self.max_width = values["width"]
            self.max_weight = values["weight"]
        elif self.restriction_type == RestrictionType.TEMPORARY:
            dates = record.temporary_dates()
            self.valid_from = dates["from"]
            self.valid_to = dates["to"]

    def __on_any_changed(self, _):
        self.any_field_changed.emit()

    @staticmethod
    def __node_id_from_point_data(point_data) -> int | None:
        if point_data is None:
            return None
        if isinstance(point_data, tuple) and len(point_data) >= 2:
            return point_data[1]
        if isinstance(point_data, dict):
            return point_data.get("node_id")
        return None
