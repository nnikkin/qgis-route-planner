import abc

from qgis_route_planner.repositories.db_connection import DbConnection


class BaseRepository(abc.ABC):
    """Базовый класс для всех репозиториев"""

    def __init__(self, db_connection: DbConnection):
        self._db = db_connection

    def execute_query(self, query: str, params: list = None) -> list[tuple]:
        """Выполнить запрос с возвратом строк (SELECT)"""
        return self._db.execute_query(query, params)

    def execute_nquery(self, query: str, params: list = None) -> None:
        """Выполнить запрос без возврата строк (INSERT/DELETE/UPDATE)"""
        return self._db.execute_nonquery(query, params)