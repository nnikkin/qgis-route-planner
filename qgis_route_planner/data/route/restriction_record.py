from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qgis_route_planner.data.models import RestrictionType


@dataclass
class RestrictionRecord:
    id: int | None = None
    restriction_type_id: int = 1
    name: str = ""
    node_id: int | None = None
    value_num: float | None = None
    value_text: str = ""
    comment: str = ""
    max_height_m: float | None = None
    max_width_m: float | None = None
    max_weight_t: float | None = None
    valid_from: str | datetime | None = None
    valid_to: str | datetime | None = None

    @staticmethod
    def dict_to_record(data: dict):
        """ Преобразовать словарь в объект RestrictionRecord"""
        return RestrictionRecord(
            id=data.get("id"),
            restriction_type_id=data.get("restriction_type_id", 1),
            name=data.get("name", ""),
            node_id=data.get("node_id"),
            value_num=data.get("value_num"),
            value_text=data.get("value_text", ""),
            comment=data.get("comment", ""),
            max_height_m=data.get("max_height_m"),
            max_width_m=data.get("max_width_m"),
            max_weight_t=data.get("max_weight_t"),
            valid_from=data.get("valid_from"),
            valid_to=data.get("valid_to"),
        )

    @staticmethod
    def record_to_dict(record) -> dict:
        """ Преобразовать объект RestrictionRecord в словарь"""
        return {
            "id": record.id,
            "restriction_type_id": record.restriction_type_id,
            "name": record.name,
            "node_id": record.node_id,
            "value_num": record.value_num,
            "value_text": record.value_text,
            "comment": record.comment,
            "max_height_m": record.max_height_m,
            "max_width_m": record.max_width_m,
            "max_weight_t": record.max_weight_t,
            "valid_from": record.valid_from,
            "valid_to": record.valid_to,
        }

    @staticmethod
    def type_to_id(rt: RestrictionType) -> int:
        """ Преобразовать тип ограничения в ID"""
        return {
            "SIMPLE": 1,
            "DIMENSION": 2,
            "TEMPORARY": 3,
        }.get(RestrictionRecord.__type_name(rt), 1)

    @staticmethod
    def id_to_type(type_id: int) -> RestrictionType:
        """ Преобразовать ID типа в enum"""
        from qgis_route_planner.data.models import RestrictionType

        return {
            1: RestrictionType.SIMPLE,
            2: RestrictionType.DIMENSION,
            3: RestrictionType.TEMPORARY,
        }.get(type_id, RestrictionType.SIMPLE)

    @staticmethod
    def id_to_type_name(type_id: int) -> str:
        """ Преобразовать ID типа в название"""
        return {
            1: "Простое",
            2: "По габаритам ТС",
            3: "По времени"
        }.get(type_id, "Простое")

    @staticmethod
    def value_text_for_type(
            restriction_type: RestrictionType,
            dimension_values: dict | None = None,
            temporary_dates: dict | None = None,
    ) -> str:
        """ Сформировать строковое значение ограничения для хранения """
        if RestrictionRecord.__type_name(restriction_type) == "DIMENSION":
            values = dimension_values or {}
            return (
                f"height={values.get('height', 0)};"
                f"width={values.get('width', 0)};"
                f"weight={values.get('weight', 0)}"
            )
        if RestrictionRecord.__type_name(restriction_type) == "TEMPORARY":
            dates = temporary_dates or {}
            return f"from={dates.get('from', '')};to={dates.get('to', '')}"
        return "simple"

    @staticmethod
    def parse_value_text(value_text: str) -> dict:
        """ Разобрать строковое значение ограничения в словарь """
        if not value_text:
            return {}
        return dict(
            part.split("=", 1)
            for part in value_text.split(";")
            if "=" in part
        )

    def dimension_values(self) -> dict:
        """ Получить значения габаритного ограничения """
        if any(value is not None for value in (self.max_height_m, self.max_width_m, self.max_weight_t)):
            return {
                "height": float(self.max_height_m or 0),
                "width": float(self.max_width_m or 0),
                "weight": float(self.max_weight_t or 0),
            }

        values = self.parse_value_text(self.value_text)
        return {
            "height": float(values.get("height", 0) or 0),
            "width": float(values.get("width", 0) or 0),
            "weight": float(values.get("weight", 0) or 0),
        }

    def temporary_dates(self) -> dict:
        """ Получить даты временного ограничения """
        if self.valid_from or self.valid_to:
            return {
                "from": self.__datetime_to_text(self.valid_from),
                "to": self.__datetime_to_text(self.valid_to),
            }

        values = self.parse_value_text(self.value_text)
        return {
            "from": values.get("from", ""),
            "to": values.get("to", ""),
        }

    @staticmethod
    def __type_name(restriction_type) -> str:
        return getattr(restriction_type, "name", str(restriction_type))

    @staticmethod
    def __datetime_to_text(value) -> str:
        if value is None:
            return ""
        if hasattr(value, "strftime"):
            return value.strftime("%Y-%m-%d %H:%M")
        return str(value)
