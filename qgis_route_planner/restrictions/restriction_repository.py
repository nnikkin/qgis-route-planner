from __future__ import annotations

import psycopg.errors

from .restriction_record import RestrictionRecord
from .restriction_type import RestrictionType
from qgis_route_planner.core.db_connection import DbConnection


class RestrictionRepository:
    def __init__(self, db: DbConnection):
        self.__db = db

    def __next_id(self) -> int:
        rows = self.__db.execute_query(
            "SELECT COALESCE(MAX(restriction_id), 0) + 1 FROM routing.restrictions"
        )
        return int(rows[0][0]) if rows else 1

    def get_all(self) -> list[dict]:
        # Собираем данные из всех трех таблиц
        rows = self.__db.execute_query("""
            SELECT
                r.restriction_id AS id,
                r.restriction_name,
                r.node_id,
                COALESCE(r.user_comment, '') AS user_comment,
                d.max_height_m,
                d.max_width_m,
                d.max_weight_t,
                t.valid_from,
                t.valid_to
            FROM routing.restrictions r
            LEFT JOIN routing.dimension_restrictions d ON r.restriction_id = d.restriction_id
            LEFT JOIN routing.temp_restrictions t ON r.restriction_id = t.restriction_id
            ORDER BY r.restriction_id DESC
        """)
        return [self.__row_to_dict(row) for row in rows]

    def get_by_id(self, restriction_id: int) -> dict | None:
        rows = self.__db.execute_query(
            """
            SELECT
                r.restriction_id AS id,
                r.restriction_name,
                r.node_id,
                COALESCE(r.user_comment, '') AS user_comment,
                d.max_height_m,
                d.max_width_m,
                d.max_weight_t,
                t.valid_from,
                t.valid_to
            FROM routing.restrictions r
            LEFT JOIN routing.dimension_restrictions d ON r.restriction_id = d.restriction_id
            LEFT JOIN routing.temp_restrictions t ON r.restriction_id = t.restriction_id
            WHERE r.restriction_id = %s
            """,
            restriction_id,
        )
        return self.__row_to_dict(rows[0]) if rows else None

    def add_restriction(self, restriction: RestrictionRecord):
        res_id = self.__next_id()

        # Вставляем в базовую таблицу
        self.__db.execute_nonquery(
            """
            INSERT INTO routing.restrictions (restriction_id, restriction_name, node_id, user_comment)
            VALUES (%s, %s, %s, %s)
            """,
            res_id,
            restriction.name,
            restriction.node_id,
            restriction.comment or "",
        )

        # Если есть габаритные данные, пишем в dimension_restrictions
        if any([restriction.max_height_m, restriction.max_width_m, restriction.max_weight_t]):
            self.__db.execute_nonquery(
                """
                INSERT INTO routing.dimension_restrictions (restriction_id, max_height_m, max_width_m, max_weight_t)
                VALUES (%s, %s, %s, %s)
                """,
                res_id,
                restriction.max_height_m,
                restriction.max_width_m,
                restriction.max_weight_t,
            )

        # Если есть временные рамки, пишем в temp_restrictions
        if restriction.valid_from or restriction.valid_to:
            self.__db.execute_nonquery(
                """
                INSERT INTO routing.temp_restrictions (restriction_id, valid_from, valid_to)
                VALUES (%s, %s, %s)
                """,
                res_id,
                restriction.valid_from,
                restriction.valid_to,
            )

    def upd_restriction(self, restriction_id: int, restriction: RestrictionRecord):
        # Обновляем базовую таблицу
        self.__db.execute_nonquery(
            """
            UPDATE routing.restrictions
            SET restriction_name = %s,
                node_id = %s,
                user_comment = %s
            WHERE restriction_id = %s
            """,
            restriction.name,
            restriction.node_id,
            restriction.comment or "",
            restriction_id,
        )

        if any([restriction.max_height_m, restriction.max_width_m, restriction.max_weight_t]):
            self.__db.execute_nonquery(
                """
                INSERT INTO routing.dimension_restrictions (restriction_id, max_height_m, max_width_m, max_weight_t)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (restriction_id) DO UPDATE
                    SET max_height_m = EXCLUDED.max_height_m,
                        max_width_m  = EXCLUDED.max_width_m,
                        max_weight_t = EXCLUDED.max_weight_t
                """,
                restriction_id, restriction.max_height_m, restriction.max_width_m, restriction.max_weight_t
            )
        else:
            self.__db.execute_nonquery(
                "DELETE FROM routing.dimension_restrictions WHERE restriction_id = %s", restriction_id
            )

        if restriction.valid_from or restriction.valid_to:
            self.__db.execute_nonquery(
                """
                INSERT INTO routing.temp_restrictions (restriction_id, valid_from, valid_to)
                VALUES (%s, %s, %s)
                ON CONFLICT (restriction_id) DO UPDATE
                    SET valid_from = EXCLUDED.valid_from,
                        valid_to   = EXCLUDED.valid_to
                """,
                restriction_id, restriction.valid_from, restriction.valid_to
            )
        else:
            self.__db.execute_nonquery(
                "DELETE FROM routing.temp_restrictions WHERE restriction_id = %s", restriction_id
            )

    def del_restriction(self, restriction_id: int):
        self.__db.execute_nonquery(
            "DELETE FROM routing.restrictions WHERE restriction_id = %s",
            restriction_id
        )

    @staticmethod
    def __row_to_dict(row) -> dict:
        restriction_type_id = RestrictionRepository.__restriction_type_id_from_row(row)
        return {
            "id": row[0],
            "name": row[1],
            "node_id": row[2],
            "comment": row[3],
            "max_height_m": row[4],
            "max_width_m": row[5],
            "max_weight_t": row[6],
            "valid_from": row[7],
            "valid_to": row[8],
            "restriction_type_id": restriction_type_id,
            "restriction_type_code": None,
            "restriction_type_name": RestrictionType.get_as_str(restriction_type_id),
            "value_num": None,
            "value_text": "",
        }

    @staticmethod
    def __restriction_type_id_from_row(row) -> int:
        has_dimension = any(value is not None for value in (row[4], row[5], row[6]))
        has_temporary = row[7] is not None or row[8] is not None
        if has_dimension:
            return RestrictionType.DIMENSION.value
        if has_temporary:
            return RestrictionType.TEMPORARY.value
        return RestrictionType.SIMPLE.value
