from qgis.PyQt.QtCore import QSettings

from ..data.vehicle import VehicleProfile, VehicleType
from ..repositories import DbConnection, VehicleProfileRepository


class SettingsService:
    """Сервис для работы с настройками плагина"""

    __SETTINGS_FILE = "qgis_route_planner.ini"
    __GROUP_DB = "database"
    __GROUP_PROFILES = "profiles"
    __KEY_ACTIVE_PROFILE = "active_profile_id"

    def __init__(self, vehicle_repo: VehicleProfileRepository):
        self.__settings: QSettings = QSettings(self.__SETTINGS_FILE, QSettings.Format.IniFormat)
        self.__vehicle_repo: VehicleProfileRepository = vehicle_repo

    # Работа с настройками БД
    def load_db_params(self) -> DbConnection | None:
        self.__settings.beginGroup(self.__GROUP_DB)

        host = self.__settings.value("host", "")
        port = self.__settings.value("port", "")
        database = self.__settings.value("database", "")
        username = self.__settings.value("username", "")
        password = self.__settings.value("password", "")
        schema = self.__settings.value("schema", "")
        self.__settings.endGroup()

        db = DbConnection(host, int(port), database, username, password, schema)
        return db if db.is_complete() else None

    def save_db_params(self, db: DbConnection):
        self.__settings.beginGroup(self.__GROUP_DB)
        self.__settings.setValue("host", db.host)
        self.__settings.setValue("port", db.port)
        self.__settings.setValue("database", db.database)
        self.__settings.setValue("username", db.username)
        self.__settings.setValue("password", db.password)
        self.__settings.setValue("schema", db.schema)
        self.__settings.endGroup()
        self.__settings.sync()


    # Работа с VehicleProfile
    def set_active_profile_id(self, profile_id: int | None):
        self.__settings.beginGroup(self.__GROUP_PROFILES)
        if profile_id is not None:
            self.__settings.setValue(self.__KEY_ACTIVE_PROFILE, profile_id)
        else:
            self.__settings.remove(self.__KEY_ACTIVE_PROFILE)
        self.__settings.endGroup()
        self.__settings.sync()

    def get_active_profile_id(self) -> int | None:
        self.__settings.beginGroup(self.__GROUP_PROFILES)
        value = self.__settings.value(self.__KEY_ACTIVE_PROFILE, None)
        self.__settings.endGroup()
        return int(value) if value is not None else None

    def create_profile(self, name: str, type: VehicleType, height: float, width: float, depth: float, weight: float) -> int:
        if not self.__vehicle_repo:
            raise Exception("Репозиторий профилей не инициализирован")
        try:
            profile = VehicleProfile(
                name=name,
                type=type.name,
                height_m=height,
                width_m=width,
                depth_m=depth,
                weight_t=weight
            )
            return self.__vehicle_repo.add_profile(profile)
        except Exception as e:
            raise Exception(f"Ошибка создания профиля: {str(e)}")

    def get_profiles(self) -> list[VehicleProfile]:
        if not self.__vehicle_repo:
            raise Exception("Репозиторий профилей не инициализирован")
        try:
            return self.__vehicle_repo.get_all()
        except Exception as e:
            raise Exception(f"Ошибка получения профилей: {str(e)}")

    def get_profile_by_id(self, profile_id: int) -> VehicleProfile:
        if not self.__vehicle_repo:
            raise Exception("Репозиторий профилей не инициализирован")
        try:
            return self.__vehicle_repo.get_by_id(profile_id)
        except Exception as e:
            raise Exception(f"Ошибка получения профиля: {str(e)}")

    def update_profile(self, profile_id: int, profile: VehicleProfile) -> bool:
        if not self.__vehicle_repo:
            raise Exception("Репозиторий профилей не инициализирован")
        try:
            self.__vehicle_repo.upd_profile(profile_id, profile)
            return True
        except Exception as e:
            raise Exception(f"Ошибка обновления профиля: {str(e)}")

    def delete_profile(self, profile_id: int) -> bool:
        if not self.__vehicle_repo:
            raise Exception("Репозиторий профилей не инициализирован")
        try:
            self.__vehicle_repo.del_profile(profile_id)
            return True
        except Exception as e:
            raise Exception(f"Ошибка удаления профиля: {str(e)}")