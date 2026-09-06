from __future__ import annotations
import psycopg.errors as psycopgError

from datetime import datetime
from psycopg.errors import Error as PsycopgError

from qgis_route_planner.restrictions import RestrictionRecord, RestrictionType
from qgis_route_planner.vehicle.vehicle_profile import VehicleProfile
from qgis_route_planner.exceptions import DbConnectionError
from qgis_route_planner.restrictions.restriction_repository import RestrictionRepository


class RestrictionService:
    """ Сервис CRUD для ограничений"""

    def __init__(self, restriction_repo: RestrictionRepository | None = None):
        self.__restriction_repo = restriction_repo

    def run_init_database(self):
        """ Инициализация БД """
        try:
            if self.__restriction_repo is not None:
                self.__restriction_repo.ensure_default_types()
        except psycopgError.Error as e:
            raise DbConnectionError(
                "Произошла ошибка при инициализации типов ограничений" + f"\n{e}",
                operation="run_init_database"
            ) from e

    def get_all_restrictions(self) -> list[dict]:
        """ Получить все ограничения из БД """
        try:
            return self.__restriction_repo.get_all()
        except PsycopgError as e:
            raise DbConnectionError(
                "Не удалось получить список всех ограничений, связанных с графом",
                operation="get_all_restrictions"
            ) from e

    def get_restriction_by_id(self, restr_id: int) -> dict | None:
        """ Получить ограничение по ID """
        try:
            return self.__restriction_repo.get_by_id(restr_id)
        except PsycopgError as e:
            raise DbConnectionError(
                f"Не удалось получить список ограничение по ID {restr_id}",
                operation="get_restriction_by_id"
            ) from e

    def get_active_restriction_node_ids(
            self,
            profile: VehicleProfile | None,
            at_dt: datetime | None = None,
    ) -> list[int]:
        """ Вернуть node_id ограничений, актуальных для текущего расчёта """
        records = [
            RestrictionRecord.dict_to_record(row)
            for row in self.get_all_restrictions()
        ]
        current_dt = at_dt or datetime.now()
        node_ids = []

        for record in records:
            if record.node_id is None:
                continue
            if self.__is_edge_dimension_restriction(record):
                continue
            if self.__is_restriction_active(record, profile, current_dt):
                node_ids.append(record.node_id)

        return list(dict.fromkeys(node_ids))

    def create_restriction(self, data: dict | RestrictionRecord) -> bool:
        """ Создать ограничение """
        try:
            self.__restriction_repo.ensure_default_types()
            record = data if isinstance(data, RestrictionRecord) else self.__dict_to_record(data)
            self.__restriction_repo.add_restriction(record)
            return True
        except PsycopgError as e:
            raise DbConnectionError(
                "Не удалось создать ограничение",
                operation="create_restriction"
            ) from e

    def update_restriction(self, restr_id: int, data: dict | RestrictionRecord) -> bool:
        """ Обновить ограничение в БД """
        try:
            self.__restriction_repo.ensure_default_types()
            record = data if isinstance(data, RestrictionRecord) else self.__dict_to_record(data)
            self.__restriction_repo.upd_restriction(restr_id, record)
            return True
        except PsycopgError as e:
            raise DbConnectionError(
                f"Не удалось обновить ограничение с ID {restr_id}",
                operation="update_restriction"
            ) from e

    def delete_restriction(self, restr_id: int) -> bool:
        """ Удалить ограничение """
        try:
            self.__restriction_repo.ensure_default_types()
            self.__restriction_repo.del_restriction(restr_id)
            return True
        except PsycopgError as e:
            raise DbConnectionError(
                f"Не удалось удалить ограничение с ID {restr_id}",
                operation="create_restriction"
            ) from e

    def __is_restriction_active(
            self,
            record: RestrictionRecord,
            profile: VehicleProfile | None,
            at_dt: datetime,
    ) -> bool:
        """ Проверка, действует ли ограничение сейчас """
        if record.restriction_type_id == RestrictionType.SIMPLE.value:
            return True
        if record.restriction_type_id == RestrictionType.TEMPORARY.value:
            return self.__is_temporary_restriction_active(record, at_dt)
        if record.restriction_type_id == RestrictionType.DIMENSION.value:
            return self.__is_dimension_restriction_active(record, profile)
        return False

    def __is_temporary_restriction_active(self, record: RestrictionRecord, at_dt: datetime) -> bool:
        """ Действует ли ограничение по времени """
        dates = record.temporary_dates()
        starts_at = self.__parse_storage_datetime(dates.get("from", ""))
        ends_at = self.__parse_storage_datetime(dates.get("to", ""))

        if starts_at and at_dt < starts_at:
            return False
        if ends_at and at_dt > ends_at:
            return False
        return bool(starts_at or ends_at)

    def __is_dimension_restriction_active(
            self,
            record: RestrictionRecord,
            profile: VehicleProfile | None,
    ) -> bool:
        """ Действует ли ограничение по габаритам """
        if profile is None:
            return False

        values = record.dimension_values()
        checks = (
            (profile.height_m, values.get("height", 0)),
            (profile.width_m, values.get("width", 0)),
            (profile.weight_t, values.get("weight", 0)),
        )
        return any(limit > 0 and actual > limit for actual, limit in checks)

    def __parse_storage_datetime(self, value: str) -> datetime | None:
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M")
        except ValueError:
            return None

    def __is_edge_dimension_restriction(self, record: RestrictionRecord) -> bool:
        if record.restriction_type_id != RestrictionType.DIMENSION.value:
            return False
        return (record.comment or "").startswith("auto:road_tags;edge_id=")

    def __dict_to_record(self, data: dict) -> RestrictionRecord:
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
