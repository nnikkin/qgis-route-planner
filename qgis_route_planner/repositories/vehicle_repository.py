from qgis_route_planner.repositories.db_connection import DbConnection
from qgis_route_planner.models.vehicle.vehicle_profile import VehicleProfile


class VehicleProfileRepository:
    def __init__(self, db: DbConnection):
        self._db = db

    def create_tables(self):
        self._db.execute_nonquery("""
        CREATE TABLE IF NOT EXISTS routing.vehicle_profiles (
        id SERIAL PRIMARY KEY,
        name VARCHAR(50) NOT NULL,
        type VARCHAR(20) DEFAULT 'car',
        height_m FLOAT DEFAULT 0,
        width_m FLOAT DEFAULT 0,
        weight_t FLOAT DEFAULT 0,
        depth_m FLOAT DEFAULT 0,
        max_speed_kmh FLOAT DEFAULT 0);
        """)

    @staticmethod
    def _row_to_profile(row: dict) -> VehicleProfile:
        return VehicleProfile(
            id=row["id"],
            name=row["name"],
            type=row.get("type", "car"),
            height_m=float(row.get("height_m", 0)),
            width_m=float(row.get("width_m", 0)),
            weight_t=float(row.get("weight_t", 0)),
            depth_m=float(row.get("depth_m", 0)),
            max_speed_kmh=float(row.get("max_speed_kmh", 0)),
        )

    def get_all(self) -> list[VehicleProfile]:
        rows = self._db.execute_query(
            "SELECT id, name, type, height_m, width_m, weight_t, depth_m, max_speed_kmh "
            "FROM routing.vehicle_profiles"
        )
        return [self._row_to_profile(row) for row in rows]

    def get_by_id(self, profile_id: int) -> VehicleProfile | None:
        rows = self._db.execute_query(
            "SELECT id, name, type, height_m, width_m, weight_t, depth_m, max_speed_kmh "
            "FROM routing.vehicle_profiles WHERE id = %s",
            [profile_id]
        )
        return self._row_to_profile(rows[0]) if rows else None

    def add_profile(self, profile: VehicleProfile) -> int:
        next_id = self._get_next_id()
        self._db.execute_nonquery(
            "INSERT INTO routing.vehicle_profiles (id, name, type, height_m, width_m, weight_t, depth_m, max_speed_kmh) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            [next_id, profile.name, profile.type, profile.height_m, profile.width_m, profile.weight_t,
             profile.depth_m, profile.max_speed_kmh]
        )
        return next_id

    def del_profile(self, profile_id: int):
        self._db.execute_nonquery(
            "DELETE FROM routing.vehicle_profiles WHERE id = %s", [profile_id]
        )

    def upd_profile(self, profile_id: int, profile: VehicleProfile):
        self._db.execute_nonquery(
            "UPDATE routing.vehicle_profiles SET name = %s, type = %s, height_m = %s, "
            "width_m = %s, weight_t = %s, depth_m = %s, max_speed_kmh = %s WHERE id = %s",
            [profile.name, profile.type, profile.height_m, profile.width_m,
             profile.weight_t, profile.depth_m, profile.max_speed_kmh, profile_id]
        )

    def _get_next_id(self) -> int:
        rows = self._db.execute_query("SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM routing.vehicle_profiles")
        return int(rows[0]["next_id"]) if rows else 1