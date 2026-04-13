from __future__ import annotations

from qgis_route_planner.database.db_connection import DbConnection

class LayerRepository:
    def __init__(self, db: DbConnection):
        self.__db = db

    @property
    def db(self) -> DbConnection:
        return self.__db

    def get_all_spatial_tables(self, schema: str) -> list:
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
        return self.__db.execute_query(query, schema)

    def get_table_columns(self, table_name: str) -> list:
        if self.__db.schema:
            query = """
                SELECT column_name, data_type
                    FROM information_schema.columns
                        WHERE table_name = %s
                            AND table_schema = %s
                ORDER BY ordinal_position
            """
            return self.__db.execute_query(query, table_name, self.__db.schema)

        query = """
            SELECT column_name, data_type
                FROM information_schema.columns
                  WHERE table_name = %s
            ORDER BY ordinal_position
        """
        return self.__db.execute_query(query, table_name)

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

    def get_all_schemas(self) -> list[tuple]:
        query = """
            SELECT schema_name
                FROM information_schema.schemata
                WHERE
                    schema_name NOT IN ('information_schema', 'pg_catalog') AND
                    schema_name NOT LIKE 'pg_%%' AND schema_name <> 'routing';
         """
        return self.__db.execute_query(query)

    def get_all_tables(self, schema: str) -> list[tuple]:
        query = """
            SELECT table_name
                FROM information_schema.tables
                WHERE
                    table_schema = %s AND
                    table_name <> 'spatial_ref_sys' AND
                    table_type = 'BASE TABLE';
        """
        return self.__db.execute_query(query, schema)
