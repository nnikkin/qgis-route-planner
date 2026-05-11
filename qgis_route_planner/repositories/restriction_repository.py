from ..data.route import RestrictionRecord
from ..repositories import DbConnection


class RestrictionRepository:
    def __init__(self, db: DbConnection):
        self.__db = db

    def create_tables(self):
        """Создаёт все нужные таблицы"""
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
                comment             TEXT DEFAULT ''
            )
        """)

        for col, definition in [
            ("name", "TEXT"),
            ("comment", "TEXT DEFAULT ''"),
        ]:
            try:
                self.__db.execute_nonquery(
                    f"ALTER TABLE routing.restrictions ADD COLUMN IF NOT EXISTS {col} {definition}"
                )
            except Exception:
                pass

    def ensure_default_types(self):
        """Создаёт таблицы и заполняет справочник типов"""
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
            self.__db.execute_nonquery(
                """
                INSERT INTO routing.restriction_types
                    (restriction_type_id, code, name)
                VALUES (%s, %s, %s)
                ON CONFLICT (restriction_type_id) DO NOTHING
                """,
                type_id, code, name,
            )

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
                COALESCE(r.comment, '') AS comment
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
                COALESCE(r.comment, '') AS comment
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
                 node_id, value_num, value_text, comment)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            self.__next_id(),
            restriction.restriction_type_id,
            restriction.name,
            restriction.node_id,
            restriction.value_num,
            restriction.value_text,
            restriction.comment or "",
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
                comment = %s
            WHERE restriction_id = %s
            """,
            restriction.restriction_type_id,
            restriction.name,
            restriction.node_id,
            restriction.value_num,
            restriction.value_text,
            restriction.comment or "",
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
        }