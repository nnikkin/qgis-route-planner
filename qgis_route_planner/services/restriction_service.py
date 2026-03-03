from qgis_route_planner.models.restrictions.restriction_record import RestrictionRecord
from qgis_route_planner.repositories.db_connection import DbConnection
from qgis_route_planner.repositories.restriction_repository import RestrictionRepository


class RestrictionService:
    """Сервис CRUD для ограничений."""

    def __init__(self, restriction_repo: RestrictionRepository | None = None):
        self.__restriction_repo = restriction_repo

    def set_restriction_repository(self, db: DbConnection | RestrictionRepository | None):
        if isinstance(db, RestrictionRepository):
            self.__restriction_repo = db
        elif isinstance(db, DbConnection):
            self.__restriction_repo = RestrictionRepository(db)
        else:
            self.__restriction_repo = None

    def ensure_default_types(self):
        if self.__restriction_repo:
            self.__restriction_repo.create_tables()
            self.__restriction_repo.ensure_default_types()

    def get_all_restrictions(self) -> list[dict]:
        if not self.__restriction_repo:
            return []
        return self.__restriction_repo.get_all()

    def get_restriction_by_id(self, restriction_id: int) -> dict | None:
        if not self.__restriction_repo:
            return None
        return self.__restriction_repo.get_by_id(restriction_id)

    def get_restriction_types(self) -> list[dict]:
        if not self.__restriction_repo:
            return []
        return self.__restriction_repo.get_types()

    def create_restriction(self, restriction: RestrictionRecord) -> bool:
        if not self.__restriction_repo:
            return False
        self.__restriction_repo.add_restriction(restriction)
        return True

    def update_restriction(self, restriction_id: int, restriction: RestrictionRecord) -> bool:
        if not self.__restriction_repo:
            return False
        self.__restriction_repo.upd_restriction(restriction_id, restriction)
        return True

    def delete_restriction(self, restriction_id: int) -> bool:
        if not self.__restriction_repo:
            return False
        self.__restriction_repo.del_restriction(restriction_id)
        return True
