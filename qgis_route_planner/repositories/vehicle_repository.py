from ..repositories import DbConnection
from ..data import VehicleProfile


class VehicleProfileRepository:
    def __init__(self, db: DbConnection):
        self.__db = db

    def create_tables(self):
        self.__db.execute_nonquery("""
        CREATE TABLE IF NOT EXISTS routing.vehicle_profiles (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50) NOT NULL,
        type VARCHAR(20) DEFAULT 'car',
        height_m FLOAT DEFAULT 0,
        width_m FLOAT DEFAULT 0,
        weight_t FLOAT DEFAULT 0,
        depth_m FLOAT DEFAULT 0);
        """)

    @staticmethod
    def __row_to_profile(row: tuple) -> VehicleProfile:
        return VehicleProfile(
            id=row[0],
            name=row[1],
            type=row[2],
            height_m=float(row[3] or 0.1),
            width_m=float(row[4] or 0.1),
            weight_t=float(row[5] or 0.1),
            depth_m=float(row[6] or 0.1),
        )

    def get_all(self) -> list[VehicleProfile]:
        rows = self.__db.execute_query(
            "SELECT id, name, type, height_m, width_m, weight_t, depth_m "
            "FROM routing.vehicle_profiles"
        )
        return [self.__row_to_profile(row) for row in rows]

    def get_by_id(self, profile_id: int) -> VehicleProfile | None:
        rows = self.__db.execute_query(
            "SELECT id, name, type, height_m, width_m, weight_t, depth_m "
            "FROM routing.vehicle_profiles WHERE id = %s",
            profile_id
        )
        return self.__row_to_profile(rows[0]) if rows else None

    def add_profile(self, profile: VehicleProfile) -> int:
        next_id = self.__get_next_id()
        self.__db.execute_nonquery(
            "INSERT INTO routing.vehicle_profiles (id, name, type, height_m, width_m, weight_t, depth_m) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            next_id, profile.name, profile.type, profile.height_m, profile.width_m, profile.weight_t,
             profile.depth_m
        )
        return next_id

    def del_profile(self, profile_id: int):
        self.__db.execute_nonquery(
            "DELETE FROM routing.vehicle_profiles WHERE id = %s", profile_id
        )

    def upd_profile(self, profile_id: int, profile: VehicleProfile):
        self.__db.execute_nonquery(
            "UPDATE routing.vehicle_profiles SET name = %s, type = %s, height_m = %s, "
            "width_m = %s, weight_t = %s, depth_m = %s WHERE id = %s",
            profile.name, profile.type, profile.height_m, profile.width_m,
             profile.weight_t, profile.depth_m, profile_id
        )

    def __get_next_id(self) -> int:
        rows = self.__db.execute_query("SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM routing.vehicle_profiles")
        if not rows or rows[0][0] is None:
            return 1
        return int(rows[0][0])