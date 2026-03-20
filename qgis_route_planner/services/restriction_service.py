from ..data.route import RestrictionRecord
from ..repositories import DbConnection, RestrictionRepository


class RestrictionService:
    """Сервис CRUD для ограничений"""

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
            self.__restriction_repo.ensure_default_types()

    def get_all_restrictions(self) -> list[dict]:
        if not self.__restriction_repo:
            return []
        return self.__restriction_repo.get_all()

    def get_restriction_by_id(self, restriction_id: int) -> dict | None:
        if not self.__restriction_repo:
            return None
        return self.__restriction_repo.get_by_id(restriction_id)

    def get_restriction_types(self) -> list:
        if not self.__restriction_repo:
            return []
        return self.__restriction_repo.get_types()

    def create_restriction(self, data: dict | RestrictionRecord) -> bool:
        if not self.__restriction_repo:
            return False
        record = data if isinstance(data, RestrictionRecord) else self.__dict_to_record(data)
        self.__restriction_repo.add_restriction(record)
        return True

    def update_restriction(self, restriction_id: int, data: dict | RestrictionRecord) -> bool:
        if not self.__restriction_repo:
            return False
        record = data if isinstance(data, RestrictionRecord) else self.__dict_to_record(data)
        self.__restriction_repo.upd_restriction(restriction_id, record)
        return True

    def delete_restriction(self, restriction_id: int) -> bool:
        if not self.__restriction_repo:
            return False
        self.__restriction_repo.del_restriction(restriction_id)
        return True

    @staticmethod
    def __dict_to_record(data: dict) -> RestrictionRecord:
        return RestrictionRecord(
            id=data.get("id"),
            restriction_type_id=data.get("restriction_type_id", 1),
            name=data.get("name", ""),
            node_id=data.get("node_id"),
            value_num=data.get("value_num"),
            value_text=data.get("value_text", ""),
            comment=data.get("comment", ""),
        )