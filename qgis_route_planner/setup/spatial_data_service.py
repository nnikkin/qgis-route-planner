from __future__ import annotations

import psycopg.errors as psycopgError
from qgis.core import QgsDataSourceUri, QgsVectorLayer

from qgis_route_planner.setup.layer_select.layer_config_model import Layer
from qgis_route_planner.exceptions import TopologyBuildError, DbConnectionError, DataImportError
from qgis_route_planner.setup.graph_repository import RoadGraphRepository
from qgis_route_planner.setup.layer_repository import LayerRepository
from qgis_route_planner.restrictions.restriction_repository import RestrictionRepository


class SpatialDataService:
    """ Сервис доступа к табличным слоям БД """

    def __init__(
            self,
            layer_repo: LayerRepository,
            graph_repo: RoadGraphRepository,
            restriction_repo: RestrictionRepository = None,
    ):
        self.__graph_repo: RoadGraphRepository = graph_repo
        self.__layer_repo: LayerRepository = layer_repo
        self.__restriction_repo: RestrictionRepository = restriction_repo

    def get_spatial_layers(self, schema: str = "public") -> list[QgsVectorLayer]:
        """ Возвращает пространственные слои из схемы """
        if not self.__layer_repo:
            return []

        try:
            tables = self.__layer_repo.get_all_spatial_tables(schema)
            layers = []

            db = self.__layer_repo.db
            for schema_name, table_name, geom_col, geom_type, srid in tables:
                _ = geom_type, srid
                uri = QgsDataSourceUri()
                uri.setConnection(
                    db.host,
                    str(db.port),
                    db.database,
                    db.username,
                    db.password,
                )
                uri.setDataSource(schema_name, table_name, geom_col)

                layer = QgsVectorLayer(uri.uri(False), f"{schema_name}.{table_name}", "postgres")
                if layer.isValid():
                    layers.append(layer)

            return layers
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
            layers = []
            db = self.__layer_repo.db
            for layer_config in layers_config:
                table_ref = layer_config.name
                if "." in table_ref:
                    schema_name, table_name = table_ref.split(".", 1)
                else:
                    schema_name = db.schema
                    table_name = table_ref

                if not schema_name:
                    continue

                columns = self.__layer_repo.get_all_spatial_tables(schema_name)
                geom_col = None
                for row_schema, row_table, row_geom_col, _geom_type, _srid in columns:
                    if row_table == table_name:
                        geom_col = row_geom_col
                        break
                if not geom_col:
                    continue

                uri = QgsDataSourceUri()
                uri.setConnection(
                    db.host,
                    str(db.port),
                    db.database,
                    db.username,
                    db.password,
                )
                uri.setDataSource(schema_name, table_name, geom_col)

                layer = QgsVectorLayer(uri.uri(False), f"{schema_name}.{table_name}", "postgres")
                if layer.isValid():
                    layers.append(layer)
            return layers
        except psycopgError.DatabaseError as e:
            raise DbConnectionError(
                "Не удалось получить информацию по выбранным таблицам слоёв",
                operation="get_selected_spatial_layers"
            ) from e

    def get_schemas(self) -> list[str]:
        """ Получение списка схем """
        try:
            tuple_list = self.__layer_repo.get_all_schemas()
            return [item[0] for item in tuple_list]
        except psycopgError.DatabaseError as e:
            raise DbConnectionError(
                "Не удалось получить список схем базы данных",
                operation="get_schemas"
            ) from e

    def get_tables(self, schema: str) -> list[str]:
        """ Получение списка таблиц по схеме """
        try:
            tuple_list = self.__layer_repo.get_all_tables(schema)
            return [item[0] for item in tuple_list]
        except psycopgError.DatabaseError as e:
            raise DbConnectionError(
                f"Не удалось получить список таблиц по схеме {schema}",
                operation="get_tables"
            ) from e

    def get_table_columns(self, table_name: str) -> list[str]:
        """ Получение списка столбцов из таблицы """
        try:
            tuple_list = self.__layer_repo.get_table_columns(table_name)
            return [item[0] for item in tuple_list]
        except psycopgError.DatabaseError as e:
            raise DbConnectionError(
                f"Не удалось получить информацию по таблице {table_name}",
                operation="get_table_columns"
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
            if self.__restriction_repo is not None:
                self.__restriction_repo.ensure_default_types()
        except psycopgError.Error as e:
            raise DbConnectionError(
                "Произошла ошибка при инициализации типов ограничений" + f"\n{e}",
                operation="run_init_database"
            ) from e

        try:
            self.__graph_repo.create_tables(layers, column_mapping)
        except (DataImportError, TopologyBuildError):
            raise
        except psycopgError.Error as e:
            raise TopologyBuildError("Не удалось построить топологию графа") from e
