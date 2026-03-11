from ..data.restrictions import RestrictionRecord
from ..repositories import DbConnection


class RestrictionRepository:
    def __init__(self, db: DbConnection):
        self.__db = db

    def create_tables(self):
        self.__db.execute_nonquery(
            """
            CREATE TABLE IF NOT EXISTS routing.restriction_types (
                restriction_type_id SMALLINT PRIMARY KEY,
                code TEXT,
                name TEXT
            )
            """
        )
        '''self.__db.execute_nonquery(
            """
            CREATE TABLE IF NOT EXISTS routing.restriction_info (
                restriction_info_id BIGINT PRIMARY KEY,
                valid_from_date DATE,
                valid_from_time TIME,
                valid_to_date DATE,
                valid_to_time TIME,
                comment TEXT
            )
            """
        )'''
        self.__db.execute_nonquery(
            """
            CREATE TABLE IF NOT EXISTS routing.restrictions (
                restriction_id BIGINT PRIMARY KEY,
                restriction_type_id SMALLINT REFERENCES routing.restriction_types(restriction_type_id),
                node_id BIGINT,
                value_num DOUBLE PRECISION,
                value_text TEXT
            )
            """
        )
        self.__db.execute_nonquery(
            """
            CREATE TABLE IF NOT EXISTS routing.turn_restrictions (
                restriction_id BIGINT PRIMARY KEY,
                via_node_id BIGINT,
                to_edge_id BIGINT,
                restriction_info_id BIGINT REFERENCES routing.restriction_info(restriction_info_id)
            )
            """
        )

    def __next_id(self, table_name: str, column_name: str) -> int:
        rows = self.__db.execute_query(
            f"SELECT COALESCE(MAX({column_name}), 0) + 1 AS next_id FROM {table_name}"
        )
        return int(rows[0][0]) if rows else 1

    def ensure_schema(self):
        self.create_tables()
        self.__db.execute_nonquery(
            "ALTER TABLE routing.restrictions ADD COLUMN IF NOT EXISTS name TEXT"
        )

    def get_all(self) -> list[dict]:
        return self.__db.execute_query(
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
                COALESCE(ri.comment, '') AS comment
            FROM routing.restrictions r
            LEFT JOIN routing.restriction_types t
                ON t.restriction_type_id = r.restriction_type_id
            LEFT JOIN routing.restriction_info ri
                ON ri.restriction_info_id = r.restriction_info_id
            ORDER BY r.restriction_id DESC
            """
        )

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
                COALESCE(ri.comment, '') AS comment
            FROM routing.restrictions r
            LEFT JOIN routing.restriction_types t
                ON t.restriction_type_id = r.restriction_type_id
            LEFT JOIN routing.restriction_info ri
                ON ri.restriction_info_id = r.restriction_info_id
            WHERE r.restriction_id = %s
            """,
            [restriction_id],
        )
        return rows[0] if rows else None

    def add_restriction(self, restriction: RestrictionRecord):
        info_id = None
        if restriction.comment:
            info_id = self.__next_id("routing.restriction_info", "restriction_info_id")
            self.__db.execute_nonquery(
                """
                INSERT INTO routing.restriction_info (
                    restriction_info_id,
                    comment
                ) VALUES (%s, %s)
                """,
                [info_id, restriction.comment],
            )

        restriction_id = self.__next_id("routing.restrictions", "restriction_id")
        self.__db.execute_nonquery(
            """
            INSERT INTO routing.restrictions (
                restriction_id,
                restriction_type_id,
                restriction_info_id,
                name,
                node_id,
                value_num,
                value_text
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            [
                restriction_id,
                restriction.restriction_type_id,
                info_id,
                restriction.name,
                restriction.node_id,
                restriction.value_num,
                restriction.value_text,
            ],
        )

    def upd_restriction(self, restriction_id: int, restriction: RestrictionRecord):
        current = self.get_by_id(restriction_id)
        info_id = None
        if current:
            info_id = current.get("restriction_info_id")

        if restriction.comment:
            if info_id is None:
                info_id = self.__next_id("routing.restriction_info", "restriction_info_id")
                self.__db.execute_nonquery(
                    """
                    INSERT INTO routing.restriction_info (
                        restriction_info_id,
                        comment
                    ) VALUES (%s, %s)
                    """,
                    [info_id, restriction.comment],
                )
            else:
                self.__db.execute_nonquery(
                    """
                    UPDATE routing.restriction_info
                    SET comment = %s
                    WHERE restriction_info_id = %s
                    """,
                    [restriction.comment, info_id],
                )

        self.__db.execute_nonquery(
            """
            UPDATE routing.restrictions
            SET restriction_type_id = %s,
                restriction_info_id = %s,
                name = %s,
                node_id = %s,
                value_num = %s,
                value_text = %s
            WHERE restriction_id = %s
            """,
            [
                restriction.restriction_type_id,
                info_id,
                restriction.name,
                restriction.node_id,
                restriction.value_num,
                restriction.value_text,
                restriction_id,
            ],
        )

    def del_restriction(self, restriction_id: int):
        current = self.get_by_id(restriction_id)
        if current and current.get("restriction_info_id"):
            self.__db.execute_nonquery(
                "DELETE FROM routing.restriction_info WHERE restriction_info_id = %s",
                [current["restriction_info_id"]],
            )

        self.__db.execute_nonquery(
            "DELETE FROM routing.restrictions WHERE restriction_id = %s",
            [restriction_id],
        )

    def get_types(self) -> list[dict]:
        return self.__db.execute_query(
            """
            SELECT restriction_type_id, code, name
            FROM routing.restriction_types
            ORDER BY restriction_type_id
            """
        )

    def ensure_default_types(self):
        self.ensure_schema()
        existing = self.get_types()
        if existing:
            return

        defaults = [
            (1, "dimension", "Габаритное"),
            (2, "temporary", "Временное")
        ]

        for restriction_type_id, code, name in defaults:
            self.__db.execute_nonquery(
                """
                INSERT INTO routing.restriction_types (
                    restriction_type_id,
                    code,
                    name
                ) VALUES (%s, %s, %s)
                """,
                [restriction_type_id, code, name],
            )
