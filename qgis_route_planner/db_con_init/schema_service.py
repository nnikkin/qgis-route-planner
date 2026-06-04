from __future__ import annotations

import psycopg.errors as psycopgError

from qgis_route_planner.core import DbConnection
from qgis_route_planner.exceptions import DbConnectionError


class SchemaService:
    """ Сервис доступа к табличным слоям БД """

    def __init__(self, db: DbConnection):
        self.__db = db

    def get_schemas(self) -> list[str]:
        try:
            query = """
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name NOT IN ('information_schema', 'pg_catalog') \
                      AND schema_name NOT LIKE 'pg_%%' \
                      AND schema_name <> 'routing'; \
                    """
            rows = self.__db.execute_query(query)
            return [row[0] for row in rows]
        except psycopgError.DatabaseError as e:
            raise DbConnectionError(
                "Не удалось получить список схем базы данных",
                operation="get_schemas"
            ) from e