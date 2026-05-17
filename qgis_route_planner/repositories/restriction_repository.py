from __future__ import annotations

import psycopg.errors

from ..data.route import RestrictionRecord
from ..repositories import DbConnection


class RestrictionRepository:
    def __init__(self, db: DbConnection):
        self.__db = db

    def create_tables(self):
        self.__db.execute_nonquery("CREATE SCHEMA IF NOT EXISTS routing")

        self.__db.execute_nonquery("""
            CREATE TABLE IF NOT EXISTS routing.restriction_types (
                restriction_type_id SMALLINT PRIMARY KEY,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL
            )
        """)

        self.__db.execute_nonquery("""
            CREATE TABLE IF NOT EXISTS routing.restrictions (
                restriction_id      BIGINT PRIMARY KEY,
                restriction_type_id SMALLINT REFERENCES routing.restriction_types(restriction_type_id),
                name                TEXT,
                node_id             BIGINT,
                value_num           DOUBLE PRECISION,
                value_text          TEXT,
                comment             TEXT DEFAULT '',
                max_height_m        DOUBLE PRECISION,
                max_width_m         DOUBLE PRECISION,
                max_weight_t        DOUBLE PRECISION,
                valid_from          TIMESTAMP,
                valid_to            TIMESTAMP
            )
        """)

        for col, definition in [
            ("name", "TEXT"),
            ("comment", "TEXT DEFAULT ''"),
            ("max_height_m", "DOUBLE PRECISION"),
            ("max_width_m", "DOUBLE PRECISION"),
            ("max_weight_t", "DOUBLE PRECISION"),
            ("valid_from", "TIMESTAMP"),
            ("valid_to", "TIMESTAMP"),
        ]:
            self.__db.execute_nonquery(
                f"ALTER TABLE routing.restrictions ADD COLUMN IF NOT EXISTS {col} {definition}"
            )
        self.__migrate_legacy_value_text()

    def ensure_default_types(self):
        self.create_tables()

        existing = {row[0] for row in self.get_types()}
        defaults = [
            (1, "simple", "Простое"),
            (2, "dimension", "Габаритное"),
            (3, "temporary", "Временное"),
        ]
        for type_id, code, name in defaults:
            if type_id in existing:
                continue
            try:
                self.__db.execute_nonquery(
                    """
                    INSERT INTO routing.restriction_types
                        (restriction_type_id, code, name)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (restriction_type_id) DO NOTHING
                    """,
                    type_id, code, name,
                )
            except psycopg.errors.DuplicateColumn:
                pass

    def __next_id(self) -> int:
        rows = self.__db.execute_query(
            "SELECT COALESCE(MAX(restriction_id), 0) + 1 FROM routing.restrictions"
        )
        return int(rows[0][0]) if rows else 1

    def get_all(self) -> list[dict]:
        rows = self.__db.execute_query("""
            SELECT
                r.restriction_id AS id,
                r.restriction_type_id,
                t.code AS restriction_type_code,
                t.name AS restriction_type_name,
                r.name,
                r.node_id,
                r.value_num,
                r.value_text,
                COALESCE(r.comment, '') AS comment,
                r.max_height_m,
                r.max_width_m,
                r.max_weight_t,
                r.valid_from,
                r.valid_to
            FROM routing.restrictions r
            LEFT JOIN routing.restriction_types t
                USING (restriction_type_id)
            ORDER BY r.restriction_id DESC
        """)
        return [self.__row_to_dict(row) for row in rows]

    def get_by_id(self, restriction_id: int) -> dict | None:
        rows = self.__db.execute_query(
            """
            SELECT
                r.restriction_id AS id,
                r.restriction_type_id,
                t.code AS restriction_type_code,
                t.name AS restriction_type_name,
                r.name,
                r.node_id,
                r.value_num,
                r.value_text,
                COALESCE(r.comment, '') AS comment,
                r.max_height_m,
                r.max_width_m,
                r.max_weight_t,
                r.valid_from,
                r.valid_to
            FROM routing.restrictions r
            LEFT JOIN routing.restriction_types t
                USING (restriction_type_id)
            WHERE r.restriction_id = %s
            """,
            restriction_id,
        )
        return self.__row_to_dict(rows[0]) if rows else None

    def add_restriction(self, restriction: RestrictionRecord):
        self.__db.execute_nonquery(
            """
            INSERT INTO routing.restrictions
                (restriction_id, restriction_type_id, name,
                 node_id, value_num, value_text, comment,
                 max_height_m, max_width_m, max_weight_t, valid_from, valid_to)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            self.__next_id(),
            restriction.restriction_type_id,
            restriction.name,
            restriction.node_id,
            restriction.value_num,
            restriction.value_text,
            restriction.comment or "",
            restriction.max_height_m,
            restriction.max_width_m,
            restriction.max_weight_t,
            restriction.valid_from,
            restriction.valid_to,
        )

    def upd_restriction(self, restriction_id: int, restriction: RestrictionRecord):
        self.__db.execute_nonquery(
            """
            UPDATE routing.restrictions
            SET restriction_type_id = %s,
                name = %s,
                node_id = %s,
                value_num = %s,
                value_text = %s,
                comment = %s,
                max_height_m = %s,
                max_width_m = %s,
                max_weight_t = %s,
                valid_from = %s,
                valid_to = %s
            WHERE restriction_id = %s
            """,
            restriction.restriction_type_id,
            restriction.name,
            restriction.node_id,
            restriction.value_num,
            restriction.value_text,
            restriction.comment or "",
            restriction.max_height_m,
            restriction.max_width_m,
            restriction.max_weight_t,
            restriction.valid_from,
            restriction.valid_to,
            restriction_id,
        )

    def del_restriction(self, restriction_id: int):
        self.__db.execute_nonquery(
            "DELETE FROM routing.restrictions WHERE restriction_id = %s",
            restriction_id
        )

    def get_types(self) -> list:
        return self.__db.execute_query(
            """
            SELECT restriction_type_id, code, name
            FROM routing.restriction_types
            ORDER BY restriction_type_id
            """
        )

    @staticmethod
    def __row_to_dict(row) -> dict:
        return {
            "id": row[0],
            "restriction_type_id": row[1],
            "restriction_type_code": row[2],
            "restriction_type_name": row[3],
            "name": row[4],
            "node_id": row[5],
            "value_num": row[6],
            "value_text": row[7],
            "comment": row[8],
            "max_height_m": row[9],
            "max_width_m": row[10],
            "max_weight_t": row[11],
            "valid_from": row[12],
            "valid_to": row[13],
        }

    def __migrate_legacy_value_text(self):
        self.__db.execute_nonquery("""
                        UPDATE routing.restrictions
                        SET
                            max_height_m = COALESCE(
                                max_height_m,
                                NULLIF(replace(substring(value_text from 'height=([0-9]+[.,]?[0-9]*)'), ',', '.'), '')::double precision
                            ),
                            max_width_m = COALESCE(
                                max_width_m,
                                NULLIF(replace(substring(value_text from 'width=([0-9]+[.,]?[0-9]*)'), ',', '.'), '')::double precision
                            ),
                            max_weight_t = COALESCE(
                                max_weight_t,
                                NULLIF(replace(substring(value_text from 'weight=([0-9]+[.,]?[0-9]*)'), ',', '.'), '')::double precision
                            ),
                            value_num = COALESCE(
                                value_num,
                                NULLIF(NULLIF(replace(substring(value_text from 'height=([0-9]+[.,]?[0-9]*)'), ',', '.'), '')::double precision, 0),
                                NULLIF(NULLIF(replace(substring(value_text from 'width=([0-9]+[.,]?[0-9]*)'), ',', '.'), '')::double precision, 0),
                                NULLIF(NULLIF(replace(substring(value_text from 'weight=([0-9]+[.,]?[0-9]*)'), ',', '.'), '')::double precision, 0)
                            )
                        WHERE restriction_type_id = 2
                          AND value_text IS NOT NULL
                          AND value_text LIKE '%=%';
                    """)
        self.__db.execute_nonquery("""
                        UPDATE routing.restrictions
                        SET value_text = ''
                        WHERE restriction_type_id = 2
                          AND value_text IS NOT NULL
                          AND value_text <> ''
                          AND (
                              max_height_m IS NOT NULL
                              OR max_width_m IS NOT NULL
                              OR max_weight_t IS NOT NULL
                          );
                    """)

        self.__db.execute_nonquery("""
                        UPDATE routing.restrictions
                        SET
                            valid_from = COALESCE(
                                valid_from,
                                NULLIF(substring(value_text from 'from=([^;]+)'), '')::timestamp
                            ),
                            valid_to = COALESCE(
                                valid_to,
                                NULLIF(substring(value_text from 'to=([^;]+)'), '')::timestamp
                            )
                        WHERE restriction_type_id = 3
                          AND value_text IS NOT NULL
                          AND value_text LIKE '%=%';
                    """)
        self.__db.execute_nonquery("""
                        UPDATE routing.restrictions
                        SET value_text = ''
                        WHERE restriction_type_id = 3
                          AND value_text IS NOT NULL
                          AND value_text <> ''
                          AND (valid_from IS NOT NULL OR valid_to IS NOT NULL);
                    """)