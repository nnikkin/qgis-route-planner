from __future__ import annotations

from qgis.PyQt.QtCore import QSettings

from qgis_route_planner.exceptions import PluginError
from qgis_route_planner.core.db_connection import DbConnection


class SettingsService:
    """ Сервис для работы с настройками плагина """

    __SETTINGS_FILE = "qgis_route_planner.ini"

    # группы настроек
    __GROUP_DB = "database"
    __GROUP_PROFILES = "profiles"
    __GROUP_WEATHER = "weather"
    __GROUP_GRAPH = "graph"

    # ключи
    __KEY_HOST = "host"
    __KEY_PORT = "port"
    __KEY_DATABASE = "database"
    __KEY_USERNAME = "username"
    __KEY_PASSWORD = "password"
    __KEY_SCHEMA = "schema"
    __KEY_ACTIVE_PROFILE = "active_profile_id"
    __KEY_POINT_SELECT_DIST = "point_select_distance"
    __KEY_BASEMAP_ENABLED = "basemap_enabled"
    __KEY_BASEMAP_URL = "basemap_url"
    __KEY_WEATHER_API_URL = "api_url"
    __KEY_WEATHER_API_KEY = "api_key"
    __KEY_FALLBACK_SEASON = "fallback_season"

    # значения по умолчанию
    __DEFAULT_POINT_SELECT_DIST = 500
    __DEFAULT_BASEMAP_ENABLED = False
    __DEFAULT_BASEMAP_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    __DEFAULT_WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
    __DEFAULT_FALLBACK_SEASON = "summer"

    def __init__(self):
        self.__settings: QSettings = QSettings(self.__SETTINGS_FILE, QSettings.Format.IniFormat)


    # Работа с настройками БД
    def load_db_params(self) -> DbConnection | None:
        self.__settings.beginGroup(self.__GROUP_DB)

        host = self.__settings.value(self.__KEY_HOST, "")
        port = self.__settings.value(self.__KEY_PORT, "")
        database = self.__settings.value(self.__KEY_DATABASE, "")
        username = self.__settings.value(self.__KEY_USERNAME, "")
        password = self.__settings.value(self.__KEY_PASSWORD, "")
        schema = self.__settings.value(self.__KEY_SCHEMA, "")
        self.__settings.endGroup()

        db = DbConnection(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
            schema=schema
        )
        return db if db.is_complete() else None

    def save_db_params(self, db: DbConnection):
        self.__settings.beginGroup(self.__GROUP_DB)
        self.__settings.setValue(self.__KEY_HOST, db.host)
        self.__settings.setValue(self.__KEY_PORT, db.port)
        self.__settings.setValue(self.__KEY_DATABASE, db.database)
        self.__settings.setValue(self.__KEY_USERNAME, db.username)
        self.__settings.setValue(self.__KEY_PASSWORD, db.password)
        self.__settings.setValue(self.__KEY_SCHEMA, db.schema)
        self.__settings.endGroup()
        self.__settings.sync()


    # Работа с настройками погодного сервиса
    def load_weather_settings(self) -> dict:
        self.__settings.beginGroup(self.__GROUP_WEATHER)
        settings = {
            self.__KEY_WEATHER_API_URL: self.__settings.value(self.__KEY_WEATHER_API_URL, self.__DEFAULT_WEATHER_API_URL),
            self.__KEY_WEATHER_API_KEY: self.__settings.value(self.__KEY_WEATHER_API_KEY, ""),
            self.__KEY_FALLBACK_SEASON: self.__settings.value(
                self.__KEY_FALLBACK_SEASON,
                self.__DEFAULT_FALLBACK_SEASON
            ),
        }
        self.__settings.endGroup()
        return settings

    def save_weather_settings(
            self,
            api_url: str,
            api_key: str,
            fallback_season: str,
    ):
        self.__settings.beginGroup(self.__GROUP_WEATHER)
        self.__settings.setValue(
            self.__KEY_WEATHER_API_URL,
            (api_url or "").strip() or self.__DEFAULT_WEATHER_API_URL
        )
        self.__settings.setValue(self.__KEY_WEATHER_API_KEY, api_key or "")
        self.__settings.setValue(self.__KEY_FALLBACK_SEASON, fallback_season or self.__DEFAULT_FALLBACK_SEASON)
        self.__settings.endGroup()
        self.__settings.sync()


    # Работа с графом
    def save_graph_settings(
            self,
            point_sel_dist: float,
            basemap_enabled: bool | None = None,
            basemap_url: str | None = None,
    ):
        try:
            self.__settings.beginGroup(self.__GROUP_GRAPH)
            self.__settings.setValue(self.__KEY_POINT_SELECT_DIST, point_sel_dist or self.__DEFAULT_POINT_SELECT_DIST)
            self.__settings.setValue(
                self.__KEY_BASEMAP_ENABLED,
                self.__DEFAULT_BASEMAP_ENABLED if basemap_enabled is None else bool(basemap_enabled)
            )
            self.__settings.setValue(
                self.__KEY_BASEMAP_URL,
                (basemap_url or "").strip() or self.__DEFAULT_BASEMAP_URL
            )
            self.__settings.endGroup()
            self.__settings.sync()
        except Exception as e:
            raise PluginError(f" {str(e)}") from e

    def load_graph_settings(self) -> dict:
        self.__settings.beginGroup(self.__GROUP_GRAPH)
        settings = {
            self.__KEY_POINT_SELECT_DIST: self.load_select_distance_setting(open_group=False),
            self.__KEY_BASEMAP_ENABLED: self.__bool_value(
                self.__settings.value(self.__KEY_BASEMAP_ENABLED, self.__DEFAULT_BASEMAP_ENABLED)
            ),
            self.__KEY_BASEMAP_URL: self.__settings.value(self.__KEY_BASEMAP_URL, self.__DEFAULT_BASEMAP_URL),
        }
        self.__settings.endGroup()
        return settings

    def load_select_distance_setting(self, open_group: bool = True) -> float:
        if open_group:
            self.__settings.beginGroup(self.__GROUP_GRAPH)
        raw = self.__settings.value(self.__KEY_POINT_SELECT_DIST, self.__DEFAULT_POINT_SELECT_DIST)
        if open_group:
            self.__settings.endGroup()
        try:
            return float(raw)
        except (TypeError, ValueError):
            return float(self.__DEFAULT_POINT_SELECT_DIST)

    @staticmethod
    def __bool_value(value) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)


    # Работа с профилями ТС
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
