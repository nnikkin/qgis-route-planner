from __future__ import annotations

import psycopg.errors as psycopgError
from qgis.core import QgsVectorLayer

from .layer_config_model import Layer
from .graph_repository import RoadGraphRepository
from .layer_repository import LayerRepository

from qgis_route_planner.exceptions import TopologyBuildError, DbConnectionError, DataImportError

class SpatialDataService:
    """ Сервис доступа к табличным слоям БД """

    def __init__(
            self,
            layer_repo: LayerRepository,
            graph_repo: RoadGraphRepository
    ):
        self.__graph_repo: RoadGraphRepository = graph_repo
        self.__layer_repo: LayerRepository = layer_repo

    def get_spatial_layers(self) -> list[QgsVectorLayer]:
        if not self.__layer_repo:
            return []
        try:
            return self.__layer_repo.get_spatial_layers()
        except psycopgError.Error as e:
            raise DbConnectionError(
                f"Ошибка загрузки информации по слоям из базы данных: {e}",
                operation="get_spatial_layers"
            ) from e

    def get_selected_spatial_layers(self, layers_config: list[Layer]) -> list[QgsVectorLayer]:
        """ Возвращает выбранные пользователем исходные слои для отображения на карте """
        if not self.__layer_repo:
            return []
        try:
            return self.__layer_repo.get_spatial_layers(layers_config)
        except psycopgError.DatabaseError as e:
            raise DbConnectionError(
                "Не удалось получить информацию по выбранным таблицам слоёв",
                operation="get_selected_spatial_layers"
            ) from e

    def get_schemas(self) -> list[str]:
        """ Получение списка схем """
        try:
            tuple_list = self.__layer_repo.get_schemas()
            return [item[0] for item in tuple_list]
        except psycopgError.DatabaseError as e:
            raise DbConnectionError(
                "Не удалось получить список схем базы данных",
                operation="get_schemas"
            ) from e

    def get_tables(self) -> list[str]:
        """ Получение списка пространственных таблиц по схеме """
        try:
            tuple_list = self.__layer_repo.get_spatial_table_names()
            return [item[0] for item in tuple_list]
        except psycopgError.DatabaseError as e:
            raise DbConnectionError(
                "Не удалось получить список пространственных таблиц",
                operation="get_tables"
            ) from e

    def get_table_columns(self, table_name: str) -> list:
        """ Получение списка столбцов из таблицы """
        try:
            return self.__layer_repo.get_table_columns(table_name)
        except psycopgError.DatabaseError as e:
            raise DbConnectionError(
                f"Не удалось получить информацию по таблице {table_name}",
                operation="get_table_columns"
            ) from e

    def validate_column_mapping(self, layers: list[Layer], column_mapping=None) -> list[str]:
        """ Проверить, что сопоставленные роли колонок подходят выбранным слоям """
        try:
            return self.__layer_repo.validate_column_mapping(layers, column_mapping)
        except psycopgError.DatabaseError as e:
            raise DbConnectionError(
                "Не удалось проверить сопоставление колонок выбранных слоёв",
                operation="validate_column_mapping"
            ) from e

    def get_first_point_source_coordinates(
            self,
            layers: list[Layer],
            column_mapping=None,
    ) -> tuple[float, float] | None:
        """ Возвращает долготу и широту первой строки выбранного источника точек """
        try:
            return self.__graph_repo.get_first_point_source_coordinates(
                layers,
                column_mapping,
            )
        except psycopgError.DatabaseError as e:
            raise DbConnectionError(
                f"Не удалось получить информацию по долготе и широте из слоя точек",
                operation="get_first_point_source_coordinates"
            ) from e

    def run_init_database(self, layers: list[Layer], column_mapping=None):
        """ Инициализация БД """
        try:
            self.__graph_repo.create_tables(layers, column_mapping)
        except (DataImportError, TopologyBuildError):
            raise
        except psycopgError.Error as e:
            raise TopologyBuildError(
                "Не удалось построить граф. Проверьте сопоставление колонок, типы данных "
                "и наличие расширений PostGIS/hstore в базе данных."
            ) from e
