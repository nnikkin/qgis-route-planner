from __future__ import annotations

from qgis.core import QgsDataSourceUri, QgsVectorLayer

from qgis_route_planner.core.db_connection import DbConnection
from qgis_route_planner.layer_config.layer_config_model import Layer


class LayerRepository:
    def __init__(self, db: DbConnection):
        self.__db = db

    @property
    def db(self) -> DbConnection:
        return self.__db

    def get_schemas(self):
        return [row[0] for row in self.__db.get_schemas()]

    def get_tables(self) -> list[tuple]:
        return self.__db.get_tables()

    def get_spatial_tables(self) -> list:
        query = """
            SELECT 
                f_table_schema, 
                f_table_name, 
                f_geometry_column, 
                type, 
                srid 
                FROM geometry_columns
                    WHERE f_table_schema = %s
        """
        return self.__db.execute_query(query, self.__db.schema)

    def get_spatial_layers(self, layers_config: list[Layer] = None):
        """ Возвращает пространственные слои из схемы """
        tables = self.get_spatial_tables()
        layers = []

        if layers_config:
            for layer_config in layers_config:
                table_ref = layer_config.name
                if "." in table_ref:
                    table_name = table_ref.split(".", 1)
                else:
                    table_name = table_ref

                geom_col = None
                for row_schema, row_table, row_geom_col, _geom_type, _srid in tables:
                    if row_table == table_name:
                        geom_col = row_geom_col
                        break
                if not geom_col:
                    continue

        for schema_name, table_name, geom_col, geom_type, srid in tables:
            _ = geom_type, srid
            uri = QgsDataSourceUri()
            uri.setConnection(
                self.__db.host,
                self.__db.port,
                self.__db.database,
                self.__db.username,
                self.__db.password,
            )
            uri.setDataSource(schema_name, table_name, geom_col)

            layer = QgsVectorLayer(uri.uri(False), f"{table_name}", "postgres")
            if layer.isValid():
                layers.append(layer)

        return layers


    def get_table_columns(self, table_name: str) -> list:
        return self.__db.get_table_columns(table_name)

    def get_layer_extent(self, table_name: str) -> tuple:
        query = f"""
            SELECT ST_XMin(extent), ST_YMin(extent), 
                   ST_XMax(extent), ST_YMax(extent)
                FROM (
                    SELECT ST_Extent(geom) as extent 
                        FROM {table_name}
            ) as subquery
        """
        result = self.__db.execute_query(query)
        if result:
            return result[0]
        return 0, 0, 0, 0
