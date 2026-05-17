import psycopg
from psycopg import sql, errors

from qgis_route_planner.exceptions import DbConnectionError


class DbConnection:
    """ Низкоуровневый класс для работы с БД """

    def __init__(self, host: str, port: str, database: str, username: str, password: str, schema: str = None):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.schema = schema

    def __create_connection(self):
        """ Создание нового соединения """
        try:
            kwargs = dict(
                host=self.host,
                port=self.port,
                dbname=self.database,
                user=self.username,
                password=self.password,
                connect_timeout=3  # в секундах
            )
            return psycopg.connect(**kwargs)
        except errors.ConnectionTimeout as e:
            raise DbConnectionError(
                "превышено время ожидания выполнения запроса",
                operation="get_schemas"
            ) from e

    def __apply_search_path(self, cursor):
        if self.schema:
            cursor.execute(
                sql.SQL("SET search_path TO {}").format(
                    sql.Identifier(self.schema)
                )
            )

    def execute_query(self, query: str | sql.Composed, *params):
        """ Выполнить запрос с возвратом результата """
        with self.__create_connection() as connection:
            with connection.cursor() as cursor:
                self.__apply_search_path(cursor)
                cursor.execute(query, params)
                return cursor.fetchall()

    def execute_nonquery(self, query: str | sql.Composed, *params):
        """ Выполнить запрос без возврата результата """
        with self.__create_connection() as connection:
            with connection.cursor() as cursor:
                self.__apply_search_path(cursor)
                cursor.execute(query, params)

    def get_schemas(self) -> list[str]:
        """ Получить список схем БД """
        try:
            query = """
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name NOT IN ('information_schema', 'pg_catalog') \
                      AND schema_name NOT LIKE 'pg_%%' \
                      AND schema_name <> 'routing'; \
                    """
            rows = self.execute_query(query)
            return [row[0] for row in rows]
        except errors.InvalidSchemaName as e:
            raise DbConnectionError(
                f"указано неверное имя схемы",
                operation="get_schemas"
            ) from e
        except errors.DatabaseError as e:
            raise DbConnectionError(
                f"не удалось получить список схем базы данных.",
                operation="get_schemas"
            ) from e
        except Exception as e:
            raise DbConnectionError(
                f"не удалось получить список схем базы данных:\n{str(e)}",
                operation="get_schemas"
            ) from e

    def get_tables(self) -> list[tuple]:
        """ Получить список таблиц в БД """
        query = """
            SELECT table_name
                FROM information_schema.tables
                WHERE
                    table_schema = %s AND
                    table_name <> 'spatial_ref_sys' AND
                    table_type = 'BASE TABLE';
        """
        return self.execute_query(query, self.schema)

    def get_table_columns(self, table_name: str) -> list:
        """ Получить поля таблицы """
        if self.schema:
            query = """
                SELECT column_name, data_type
                    FROM information_schema.columns
                        WHERE table_name = %s
                            AND table_schema = %s
                ORDER BY ordinal_position
            """
            return self.execute_query(query, table_name, self.schema)

        query = """
            SELECT column_name, data_type
                FROM information_schema.columns
                  WHERE table_name = %s
            ORDER BY ordinal_position
        """
        return self.execute_query(query, table_name)

    def test_connection(self) -> bool:
        """ Проверка возможности подключения """
        return True if self.execute_query("SELECT 1") else False

    def has_required_params(self) -> bool:
        return all([self.host, self.port, self.database, self.username])

    def is_complete(self) -> bool:
        return self.has_required_params() and self.schema is not None