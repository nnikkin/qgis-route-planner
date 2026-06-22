from __future__ import annotations

import psycopg.errors
from psycopg import sql
from qgis.core import QgsDataSourceUri, QgsVectorLayer

from qgis_route_planner.core.db_connection import DbConnection
from qgis_route_planner.layer_config.column_role import ColumnRole
from qgis_route_planner.layer_config.layer_config_model import Layer
from qgis_route_planner.layer_config.layer_role import LayerRole


class LayerRepository:
    __TEXT_TYPES = {"text", "character varying", "character", "varchar", "char"}
    __NUMERIC_ROLES = {
        ColumnRole.MAX_HEIGHT,
        ColumnRole.MAX_WIDTH,
        ColumnRole.MAX_WEIGHT,
        ColumnRole.MAX_SPEED,
        ColumnRole.LANES_FORWARD,
        ColumnRole.LANES_BACKWARD,
    }
    __EXPECTED_HIGHWAYS = (
        "primary", "secondary", "tertiary", "motorway", "trunk",
        "primary_link", "secondary_link", "tertiary_link", "motorway_link", "trunk_link",
        "service", "road", "unclassified", "residential", "living_street",
    )
    __GEOMETRY_TYPES_BY_ROLE = {
        LayerRole.ROADS: {"LINESTRING", "MULTILINESTRING"},
        LayerRole.POINTS: {"POINT", "MULTIPOINT"},
        LayerRole.PARKING: {"POLYGON", "MULTIPOLYGON"},
        LayerRole.PIPING: {"LINESTRING", "MULTILINESTRING"},
        LayerRole.FOR_CONTEXT: {"POINT", "MULTIPOINT", "LINESTRING", "MULTILINESTRING", "POLYGON", "MULTIPOLYGON"},
    }

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

    def get_spatial_table_names(self) -> list[tuple[str]]:
        query = """
            SELECT DISTINCT f_table_name
            FROM geometry_columns
            WHERE f_table_schema = %s
            ORDER BY f_table_name
        """
        return self.__db.execute_query(query, self.__db.schema)

    def get_spatial_layers(self, layers_config: list[Layer] = None):
        """ Возвращает пространственные слои из схемы """
        tables = self.get_spatial_tables()
        layers = []
        selected_names = None
        roles_by_name = {}

        if layers_config:
            selected_names = {layer_config.name.split(".", 1)[-1] for layer_config in layers_config}
            for layer_config in layers_config:
                table_ref = layer_config.name
                if "." in table_ref:
                    table_name = table_ref.split(".", 1)[1]
                else:
                    table_name = table_ref
                roles_by_name[table_name] = layer_config.role

                geom_col = None
                for row_schema, row_table, row_geom_col, _geom_type, _srid in tables:
                    if row_table == table_name:
                        geom_col = row_geom_col
                        break
                if not geom_col:
                    continue

        for schema_name, table_name, geom_col, geom_type, srid in tables:
            if selected_names is not None and table_name not in selected_names:
                continue

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
                role = roles_by_name.get(table_name)
                if role:
                    layer.setCustomProperty("qgis_route_planner/layer_role", role.name)
                elif table_name == "graph_edges":
                    layer.setCustomProperty("qgis_route_planner/layer_role", LayerRole.ROADS.name)
                layers.append(layer)

        return layers


    def get_table_columns(self, table_name: str) -> list:
        return self.__db.get_table_columns(table_name)

    def validate_column_mapping(
            self,
            layers: list[Layer],
            column_mapping: dict[str, dict[ColumnRole, str | None]] | None,
    ) -> list[str]:
        errors = []
        column_mapping = column_mapping or {}

        for layer in layers:
            mapping = column_mapping.get(layer.name, {})
            columns = self.__table_columns_by_name(layer.name)
            columns_by_lower = {name.lower(): (name, data_type) for name, data_type in columns.items()}

            for role, column_name in mapping.items():
                if not column_name:
                    continue
                if column_name.lower() not in columns_by_lower:
                    errors.append(
                        f"{layer.name}: колонка '{column_name}' для роли '{role.value}' не найдена в таблице."
                    )

            geom_col = mapping.get(ColumnRole.GEOMETRY)
            if geom_col and geom_col.lower() in columns_by_lower:
                errors.extend(self.__validate_geometry_column(layer, geom_col))

            primary_key_col = mapping.get(ColumnRole.PRIMARY_KEY)
            if primary_key_col and primary_key_col.lower() in columns_by_lower:
                errors.extend(self.__validate_primary_key_column(layer.name, primary_key_col))

            highway_col = mapping.get(ColumnRole.HIGHWAY)
            if highway_col and highway_col.lower() in columns_by_lower:
                actual_col, data_type = columns_by_lower[highway_col.lower()]
                errors.extend(self.__validate_highway_column(layer.name, actual_col, data_type))

            for role in self.__NUMERIC_ROLES:
                column_name = mapping.get(role)
                if column_name and column_name.lower() in columns_by_lower:
                    actual_col, _data_type = columns_by_lower[column_name.lower()]
                    errors.extend(self.__validate_numeric_column(layer.name, actual_col, role))

            other_col = mapping.get(ColumnRole.OTHER)
            if other_col and other_col.lower() in columns_by_lower:
                actual_col, _data_type = columns_by_lower[other_col.lower()]
                errors.extend(self.__validate_hstore_column(layer.name, actual_col))

        return errors

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

    def __table_parts(self, table_name: str) -> tuple[str | None, str]:
        if "." in table_name:
            schema_name, plain_table_name = table_name.split(".", 1)
            return schema_name, plain_table_name
        return self.__db.schema, table_name

    def __qualified_table(self, table_name: str):
        schema_name, plain_table_name = self.__table_parts(table_name)
        if schema_name:
            return sql.SQL("{}.{}").format(
                sql.Identifier(schema_name),
                sql.Identifier(plain_table_name),
            )
        return sql.Identifier(plain_table_name)

    def __table_columns_by_name(self, table_name: str) -> dict[str, str]:
        schema_name, plain_table_name = self.__table_parts(table_name)
        if schema_name:
            query = """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
            """
            rows = self.__db.execute_query(query, schema_name, plain_table_name)
        else:
            query = """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = %s
            """
            rows = self.__db.execute_query(query, plain_table_name)
        return {name: data_type for name, data_type in rows}

    def __validate_geometry_column(self, layer: Layer, column_name: str) -> list[str]:
        schema_name, plain_table_name = self.__table_parts(layer.name)
        if not schema_name:
            return []

        rows = self.__db.execute_query(
            """
            SELECT type
            FROM geometry_columns
            WHERE f_table_schema = %s
              AND f_table_name = %s
              AND lower(f_geometry_column) = lower(%s)
            LIMIT 1
            """,
            schema_name,
            plain_table_name,
            column_name,
        )
        if not rows:
            return [
                f"{layer.name}: колонка '{column_name}' для роли '{ColumnRole.GEOMETRY.value}' "
                "не зарегистрирована как геометрия."
            ]

        geometry_type = self.__normalize_geometry_type(rows[0][0])
        if geometry_type == "GEOMETRY":
            geometry_type = self.__sample_geometry_type(layer.name, column_name)
        expected_types = self.__GEOMETRY_TYPES_BY_ROLE.get(layer.role, set())
        if expected_types and geometry_type not in expected_types:
            expected_text = ", ".join(sorted(expected_types))
            return [
                f"{layer.name}: колонка '{column_name}' имеет тип геометрии {geometry_type}, "
                f"ожидалось: {expected_text}."
            ]
        return []

    def __sample_geometry_type(self, table_name: str, column_name: str) -> str:
        rows = self.__db.execute_query(
            sql.SQL("""
                SELECT ST_GeometryType({col})
                FROM {table}
                WHERE {col} IS NOT NULL
                LIMIT 1
            """).format(
                table=self.__qualified_table(table_name),
                col=sql.Identifier(column_name),
            )
        )
        if not rows or not rows[0][0]:
            return "GEOMETRY"
        return self.__normalize_geometry_type(rows[0][0])

    @staticmethod
    def __normalize_geometry_type(value) -> str:
        geometry_type = str(value or "").upper()
        if geometry_type.startswith("ST_"):
            geometry_type = geometry_type[3:]
        return geometry_type

    def __validate_primary_key_column(self, table_name: str, column_name: str) -> list[str]:
        table = self.__qualified_table(table_name)
        col = sql.Identifier(column_name)
        errors = []

        rows = self.__db.execute_query(
            sql.SQL("""
                SELECT COUNT(*) AS total_count,
                       COUNT({col}) AS filled_count,
                       COUNT(DISTINCT {col}) AS distinct_count
                FROM {table}
            """).format(table=table, col=col)
        )
        total_count, filled_count, distinct_count = rows[0] if rows else (0, 0, 0)
        if total_count != filled_count:
            errors.append(
                f"{table_name}: колонка '{column_name}' для роли '{ColumnRole.PRIMARY_KEY.value}' содержит пустые значения."
            )
        if filled_count != distinct_count:
            errors.append(
                f"{table_name}: колонка '{column_name}' для роли '{ColumnRole.PRIMARY_KEY.value}' содержит дубликаты."
            )

        rows = self.__db.execute_query(
            sql.SQL("""
                SELECT {col}
                FROM {table}
                WHERE {col} IS NOT NULL
                  AND NOT ({col}::text ~ '^[+-]?[0-9]+$')
                LIMIT 1
            """).format(table=table, col=col)
        )
        if rows:
            errors.append(
                f"{table_name}: колонка '{column_name}' для роли '{ColumnRole.PRIMARY_KEY.value}' "
                "должна приводиться к целому числу."
            )
        return errors

    def __validate_highway_column(self, table_name: str, column_name: str, data_type: str) -> list[str]:
        errors = []
        if data_type not in self.__TEXT_TYPES:
            errors.append(
                f"{table_name}: колонка '{column_name}' для роли '{ColumnRole.HIGHWAY.value}' "
                f"имеет тип {data_type}, ожидается текстовая колонка."
            )

        rows = self.__db.execute_query(
            sql.SQL("""
                SELECT COUNT(*)
                FROM {table}
                WHERE lower({col}::text) = ANY(%s::text[])
            """).format(
                table=self.__qualified_table(table_name),
                col=sql.Identifier(column_name),
            ),
            list(self.__EXPECTED_HIGHWAYS),
        )
        if not rows or rows[0][0] == 0:
            errors.append(
                f"{table_name}: колонка '{column_name}' для роли '{ColumnRole.HIGHWAY.value}' "
                "не содержит ожидаемых классов дорог."
            )
        return errors

    def __validate_numeric_column(self, table_name: str, column_name: str, role: ColumnRole) -> list[str]:
        rows = self.__db.execute_query(
            sql.SQL("""
                SELECT {col}
                FROM {table}
                WHERE {col} IS NOT NULL
                  AND NULLIF(
                        regexp_replace(
                            replace({col}::text, ',', '.'),
                            '[^0-9.]',
                            '',
                            'g'
                        ),
                        ''
                  ) IS NULL
                LIMIT 1
            """).format(
                table=self.__qualified_table(table_name),
                col=sql.Identifier(column_name),
            )
        )
        if rows:
            return [
                f"{table_name}: колонка '{column_name}' для роли '{role.value}' "
                "должна содержать число или текст, из которого можно извлечь число."
            ]
        return []

    def __validate_hstore_column(self, table_name: str, column_name: str) -> list[str]:
        try:
            self.__db.execute_query(
                sql.SQL("""
                    SELECT {col}::hstore
                    FROM {table}
                    WHERE {col} IS NOT NULL
                    LIMIT 1
                """).format(
                    table=self.__qualified_table(table_name),
                    col=sql.Identifier(column_name),
                )
            )
        except psycopg.errors.Error:
            return [
                f"{table_name}: колонка '{column_name}' для роли '{ColumnRole.OTHER.value}' "
                "не приводится к hstore."
            ]
        return []
