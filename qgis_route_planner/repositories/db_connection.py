import psycopg
from psycopg import sql

class DbConnection:
    """Низкоуровневый класс для работы с БД"""

    def __init__(self, host: str, port: int, database: str, username: str, password: str, schema: str = None):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.schema = schema

    def __create_connection(self):
        """Создание нового соединение"""
        kwargs = dict(
            host=self.host,
            port=self.port,
            dbname=self.database,
            user=self.username,
            password=self.password,
            connect_timeout=3  # 3 seconds
        )
        return psycopg.connect(**kwargs)

    def __apply_search_path(self, cursor):
        if self.schema:
            cursor.execute(
                sql.SQL("SET search_path TO {}").format(
                    sql.Identifier(self.schema)
                )
            )

    def execute_query(self, query: str | sql.Composed, *params):
        """Выполнить запрос с возвратом результата"""
        with self.__create_connection() as connection:
            with connection.cursor() as cursor:
                self.__apply_search_path(cursor)
                cursor.execute(query, params)
                return cursor.fetchall()

    def execute_nonquery(self, query: str | sql.Composed, *params):
        """Выполнить запрос без возврата результата"""
        with self.__create_connection() as connection:
            with connection.cursor() as cursor:
                self.__apply_search_path(cursor)
                cursor.execute(query, params)

    def test_connection(self) -> bool:
        """Проверка возможности подключения"""
        try:
            return True if self.execute_query("SELECT 1") else False
        except:
            return False

    def has_required_params(self) -> bool:
        return all([self.host, self.port, self.database, self.username])

    def is_complete(self):
        return self.has_required_params and self.schema is not None