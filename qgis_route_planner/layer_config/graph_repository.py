from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from qgis_route_planner.vehicle import VehicleProfile, VehicleType

import psycopg.errors
from psycopg import sql

from .layer_config_model import Layer
from .layer_role import LayerRole
from .column_role import ColumnRole

from qgis_route_planner.exceptions import NodeNotFoundError, TopologyBuildError
from qgis_route_planner.vehicle import VehicleType
from qgis_route_planner.core.db_connection import DbConnection


class RoadGraphRepository:
    """ Репозиторий для работы с таблицами графа """
    def __init__(self, db: DbConnection):
        self.__db = db

    def __create_edges_table(self):
        """ Создание таблицы routing.graph_edges """
        self.__db.execute_nonquery("""
            CREATE TABLE IF NOT EXISTS routing.graph_edges (
                edge_id BIGINT PRIMARY KEY,
                geom GEOMETRY(LineString, 4326),
                source BIGINT REFERENCES routing.graph_nodes(node_id),
                source_x DOUBLE PRECISION,
                source_y DOUBLE PRECISION,
                target BIGINT REFERENCES routing.graph_nodes(node_id),
                target_x DOUBLE PRECISION,
                target_y DOUBLE PRECISION,
                cost DOUBLE PRECISION,
                reverse_cost DOUBLE PRECISION,
                point_cost_penalty DOUBLE PRECISION DEFAULT 0.0,
                length_m DOUBLE PRECISION
            );
        """)

        self.__db.execute_nonquery("""
           CREATE TABLE IF NOT EXISTS routing.graph_edge_info
           (
               id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
               edge_id BIGINT REFERENCES routing.graph_edges (edge_id) ON DELETE CASCADE ON UPDATE CASCADE,
               road_class_id SMALLINT REFERENCES routing.road_classes (class_id),
               name TEXT,
               is_oneway BOOLEAN,
               hgv BOOLEAN,
               bridge BOOLEAN DEFAULT FALSE,
               lanes_forward INTEGER,
               lanes_backward INTEGER,
               max_height FLOAT,
               max_width_m DOUBLE PRECISION,
               max_weight_t DOUBLE PRECISION,
               max_speed_kmh DOUBLE PRECISION,
               avg_speed_estimated DOUBLE PRECISION,
               max_speed_practical_kmh DOUBLE PRECISION
           );
           """)
        self.__ensure_edges_columns()

    def __ensure_edges_columns(self):
        for col, typ in [
            ("geom", "GEOMETRY(LineString, 4326)"),
            ("target", "BIGINT"),
            ("source", "BIGINT"),
            ("target_x", "DOUBLE PRECISION"),
            ("target_y", "DOUBLE PRECISION"),
            ("source_x", "DOUBLE PRECISION"),
            ("source_y", "DOUBLE PRECISION"),
            ("cost", "DOUBLE PRECISION"),
            ("reverse_cost", "DOUBLE PRECISION"),
            ("point_cost_penalty", "DOUBLE PRECISION")
        ]:
            try:
                self.__db.execute_nonquery(
                    f"ALTER TABLE routing.graph_edges ADD COLUMN IF NOT EXISTS {col} {typ};"
                )
            except psycopg.errors.DuplicateColumn:
                pass

        for col, typ in [
            ("max_height_m", "DOUBLE PRECISION"),
            ("max_width_m", "DOUBLE PRECISION"),
            ("max_weight_t", "DOUBLE PRECISION"),
            ("bridge", "BOOLEAN DEFAULT FALSE"),
            ("lanes_forward", "INTEGER"),
            ("lanes_backward", "INTEGER"),
            ("max_speed_practical_kmh", "DOUBLE PRECISION")
        ]:
            try:
                self.__db.execute_nonquery(
                    f"ALTER TABLE routing.graph_edge_info ADD COLUMN IF NOT EXISTS {col} {typ};"
                )
            except psycopg.errors.DuplicateColumn:
                pass

    def __create_nodes_table(self):
        """ Создание таблицы routing.graph_nodes """
        self.__db.execute_nonquery("""
            CREATE TABLE IF NOT EXISTS routing.graph_nodes (
                node_id BIGINT PRIMARY KEY,
                in_edges BIGINT[],
                out_edges BIGINT[],
                x DOUBLE PRECISION,
                y DOUBLE PRECISION,
                geom GEOMETRY(Point, 4326),
                access TEXT DEFAULT NULL,
                motorcar TEXT DEFAULT NULL,
                traffic_calming TEXT DEFAULT NULL,
                crossing TEXT DEFAULT NULL,
                traffic_sign TEXT DEFAULT NULL,
                node_cost_penalty DOUBLE PRECISION DEFAULT 0.0
            );
        """)

    def __create_road_class_table(self):
        """ Создание таблицы routing.road_classes """
        self.__db.execute_nonquery("""
            CREATE TABLE IF NOT EXISTS routing.road_classes (
                class_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                class_name VARCHAR(20) UNIQUE NOT NULL
            );
        """)

    def __fill_edges_source_target(self):
        """ Заполнение столбцов source и target таблицы routing.graph_edges """
        self.__db.execute_nonquery("""
            WITH source_nodes AS (
                SELECT e.edge_id, v.node_id, v.x, v.y
                FROM routing.graph_edges e
                JOIN LATERAL (
                    SELECT node_id, x, y, geom
                    FROM routing.graph_nodes
                    WHERE ST_DWithin(ST_StartPoint(e.geom), geom, 1e-8)
                    ORDER BY ST_StartPoint(e.geom) <-> geom
                    LIMIT 1
                ) v ON TRUE
                WHERE e.geom IS NOT NULL
            )
            UPDATE routing.graph_edges AS e
            SET source = v.node_id, source_x = v.x, source_y = v.y
            FROM source_nodes AS v
            WHERE e.edge_id = v.edge_id;
         """)

        self.__db.execute_nonquery("""
            WITH target_nodes AS (
                SELECT e.edge_id, v.node_id, v.x, v.y
                FROM routing.graph_edges e
                JOIN LATERAL (
                    SELECT node_id, x, y, geom
                    FROM routing.graph_nodes
                    WHERE ST_DWithin(ST_EndPoint(e.geom), geom, 1e-8)
                    ORDER BY ST_EndPoint(e.geom) <-> geom
                    LIMIT 1
                ) v ON TRUE
                WHERE e.geom IS NOT NULL
            )
            UPDATE routing.graph_edges AS e
            SET target = v.node_id, target_x = v.x, target_y = v.y
            FROM target_nodes AS v
            WHERE e.edge_id = v.edge_id;
        """)

    def __extract_vertices(self):
        """ Заполнение таблицы routing.graph_nodes """
        self.__db.execute_nonquery("""
            INSERT INTO routing.graph_nodes (node_id, in_edges, out_edges, x, y, geom)
            SELECT id, in_edges, out_edges, x, y, geom
            FROM pgr_extractVertices(
                'SELECT edge_id as id, geom FROM routing.graph_edges ORDER BY edge_id'
            )
            ON CONFLICT (node_id) DO NOTHING;
        """)

    def __rebuild_vertices(self):
        """ Пересоздание вершин из текущего набора рёбер. """
        self.__db.execute_nonquery("""
            UPDATE routing.graph_edges
            SET
                source = NULL,
                source_x = NULL,
                source_y = NULL,
                target = NULL,
                target_x = NULL,
                target_y = NULL;
        """)
        self.__db.execute_nonquery("DELETE FROM routing.graph_nodes;")
        self.__extract_vertices()

    def __assert_complete_topology(self):
        result = self.__db.execute_query("""
            SELECT COUNT(*)
            FROM routing.graph_edges
            WHERE source IS NULL OR target IS NULL;
        """)
        missing_count = result[0][0] if result else 0
        if missing_count:
            raise TopologyBuildError(
                f"Не удалось построить топологию: у {missing_count} рёбер не заполнены source/target."
            )

    def __remove_orphan_nodes(self):
        """ Удаление изолированных вершин из routing.graph_nodes """
        self.__db.execute_nonquery("""
            DELETE FROM routing.graph_nodes n
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM routing.graph_edges e
                    WHERE e.source = n.node_id OR e.target = n.node_id
                );
        """)

    def __fill_edges_cost(self):
        """ Заполнение весов в routing.graph_nodes """
        self.__db.execute_nonquery("""
            UPDATE routing.graph_edges e
            SET
                length_m = ST_Length(e.geom::geography, true),
                cost = ST_Length(e.geom::geography, true) / (NULLIF(info.avg_speed_estimated, 0) / 3.6),
                reverse_cost = CASE
                    WHEN info.is_oneway = TRUE THEN -1
                    ELSE ST_Length(e.geom::geography, true) / (NULLIF(info.avg_speed_estimated, 0) / 3.6)
                END
            FROM routing.graph_edge_info info
            WHERE e.edge_id = info.edge_id;
        """)

    def __create_road_point_events_table(self):
        """
            Создание таблицы routing.road_point_events.
            Хранит точечные объекты, импортированные из точечных слоёв
        """
        self.__db.execute_nonquery("""
            CREATE TABLE IF NOT EXISTS routing.road_point_events (
                event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                source_layer TEXT,
                source_id BIGINT,
                nearest_edge_id BIGINT,
                nearest_node_id BIGINT,
                geom GEOMETRY(Point, 4326),
                event_type TEXT,
                max_speed_kmh DOUBLE PRECISION,
                access TEXT,
                motorcar TEXT,
                traffic_calming TEXT,
                crossing TEXT,
                traffic_signal BOOLEAN DEFAULT FALSE,
                tags TEXT,
                cost_penalty DOUBLE PRECISION DEFAULT 0.0
            );
        """)

    def __create_parking_areas_table(self):
        """ Создание таблицы парковок routing.parking_areas """
        self.__db.execute_nonquery("""
            CREATE TABLE IF NOT EXISTS routing.parking_areas (
                parking_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                source_layer TEXT,
                source_id BIGINT,
                name TEXT,
                geom GEOMETRY(MultiPolygon, 4326)
            );
        """)

    def __fill_avg_speed(self):
        """ Заполнение средней скорости """
        self.__db.execute_nonquery("""
            UPDATE routing.graph_edge_info info
            SET avg_speed_estimated = CASE
                WHEN info.max_speed_practical_kmh > 0 THEN info.max_speed_practical_kmh
                WHEN info.max_speed_kmh > 0 THEN GREATEST(info.max_speed_kmh * 0.55, 10)
                WHEN c.class_name = 'motorway' THEN 80
                WHEN c.class_name = 'motorway_link' THEN 40
                WHEN c.class_name = 'trunk' THEN 55
                WHEN c.class_name = 'trunk_link' THEN 35
                WHEN c.class_name = 'primary' THEN 35
                WHEN c.class_name = 'primary_link' THEN 25
                WHEN c.class_name = 'secondary' THEN 30
                WHEN c.class_name = 'secondary_link' THEN 22
                WHEN c.class_name = 'tertiary' THEN 25
                WHEN c.class_name = 'tertiary_link' THEN 20
                WHEN c.class_name = 'residential' THEN 20
                WHEN c.class_name = 'living_street' THEN 10
                WHEN c.class_name = 'unclassified' THEN 20
                WHEN c.class_name = 'service' THEN 15
                WHEN c.class_name = 'road' THEN 20
                ELSE 20
            END
            FROM routing.road_classes c
            WHERE info.road_class_id = c.class_id
        """)

    def __create_indexes(self):
        self.__db.execute_nonquery("""
            CREATE INDEX IF NOT EXISTS idx_graph_edges_geom
            ON routing.graph_edges USING GIST (geom);
        """)
        self.__db.execute_nonquery("""
            CREATE INDEX IF NOT EXISTS idx_graph_nodes_geom
            ON routing.graph_nodes USING GIST (geom);
        """)

    def __keep_largest_connected_components(self):
        self.__db.execute_nonquery("""
            WITH components AS (
                SELECT *
                FROM pgr_connectedComponents(
                    'SELECT edge_id AS id, source, target, 1 AS cost, 1 AS reverse_cost
                     FROM routing.graph_edges
                     WHERE source IS NOT NULL AND target IS NOT NULL'
                )
            ),
            main_component AS (
                SELECT component
                FROM components
                GROUP BY component
                ORDER BY COUNT(*) DESC
                LIMIT 1
            ),
            bad_nodes AS (
                SELECT node
                FROM components
                WHERE component <> (SELECT component FROM main_component)
            )
            DELETE FROM routing.graph_edges e
            WHERE e.source IN (SELECT node FROM bad_nodes)
               OR e.target IN (SELECT node FROM bad_nodes);
        """)

    def create_topology(self):
        """ Перестроить топологию графа """
        table_exists = self.__db.execute_query("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'graph_edges' AND table_schema = 'routing'
            );
        """)

        if not table_exists:
            raise TopologyBuildError("Таблица graph_edges не найдена. Сначала загрузите данные!")
        else:
            count = self.__db.execute_query("SELECT COUNT(*) FROM routing.graph_edges;")
            if count and count[0][0] == 0:
                raise TopologyBuildError("Нет данных в таблице graph_edges. Сначала загрузите данные!")

        self.__rebuild_vertices()
        self.__fill_edges_source_target()
        self.__assert_complete_topology()
        #self.__keep_largest_connected_components()
        self.__remove_orphan_nodes()
        self.__fill_avg_speed()
        self.__fill_edges_cost()

    def create_tables(
            self,
            layers: list[Layer],
            column_mapping: dict[str, dict[ColumnRole, str | None]] | None = None,
    ):
        """ Создание таблиц и заполнение графа из слоёв дорог """
        for cmd in [
            'CREATE SCHEMA IF NOT EXISTS routing;',
            'CREATE EXTENSION IF NOT EXISTS postgis;',
            'CREATE EXTENSION IF NOT EXISTS pgrouting;',
            'CREATE EXTENSION IF NOT EXISTS hstore;'
        ]:
            self.__db.execute_nonquery(cmd)

        self.__create_nodes_table()
        self.__create_road_class_table()
        self.__create_edges_table()
        self.__create_road_point_events_table()
        self.__create_parking_areas_table()
        self.__insert_edges_from_mapping(layers, column_mapping)

        count = self.__db.execute_query("SELECT COUNT(*) FROM routing.graph_nodes;")[0][0]
        if count == 0:
            self.__extract_vertices()

        self.__create_indexes()
        self.create_topology()
        self.enrich_edges_from_points(self.__get_layers_by_role(layers, LayerRole.POINTS), column_mapping)
        self.create_parking_areas(self.__get_layers_by_role(layers, LayerRole.PARKING), column_mapping)

        self.create_restriction_tables()
        self.create_restrictions_from_roads()
        self.create_restrictions_from_pipes(self.__get_layers_by_role(layers, LayerRole.PIPING), column_mapping)

    def create_restriction_tables(self):
        self.__db.execute_nonquery("CREATE SCHEMA IF NOT EXISTS routing")

        # Базовая таблица ограничений (включая простые ограничения 'simple')
        self.__db.execute_nonquery("""
            CREATE TABLE IF NOT EXISTS routing.restrictions (
                restriction_id      BIGINT PRIMARY KEY,
                node_id             BIGINT,
                restriction_name    TEXT,
                user_comment        TEXT DEFAULT ''
            )
        """)

        # Таблица ограничений по габаритам
        self.__db.execute_nonquery("""
            CREATE TABLE IF NOT EXISTS routing.dimension_restrictions (
                restriction_id BIGINT PRIMARY KEY REFERENCES routing.restrictions(restriction_id) ON DELETE CASCADE,
                max_height_m   DOUBLE PRECISION,
                max_width_m    DOUBLE PRECISION,
                max_depth_m    DOUBLE PRECISION,
                max_weight_t   DOUBLE PRECISION
            )
        """)

        # Таблица временных ограничений
        self.__db.execute_nonquery("""
            CREATE TABLE IF NOT EXISTS routing.temp_restrictions (
                restriction_id BIGINT PRIMARY KEY REFERENCES routing.restrictions(restriction_id) ON DELETE CASCADE,
                valid_from     TIMESTAMP,
                valid_to       TIMESTAMP
            )
        """)

    def __insert_edges_from_mapping(
            self,
            layers: list[Layer],
            column_mapping: dict[str, dict[ColumnRole, str | None]] | None,
    ):
        """ Заполнение таблиц graph_edges и graph_edge_info рёбрами """
        line_table = self.__get_line_table(layers)
        if line_table is None:
            raise TopologyBuildError("Не выбрана таблица с линейной геометрией для построения графа.")

        # Очищаем таблицы
        self.__db.execute_nonquery("TRUNCATE routing.graph_edges CASCADE")
        self.__db.execute_nonquery("DELETE FROM routing.graph_nodes")
        self.__db.execute_nonquery("TRUNCATE routing.road_classes CASCADE")

        table_mapping = column_mapping.get(line_table, {})
        edge_id_col = table_mapping.get(ColumnRole.PRIMARY_KEY)
        geom_col = table_mapping.get(ColumnRole.GEOMETRY)
        highway_col = table_mapping.get(ColumnRole.HIGHWAY)
        name_col = table_mapping.get(ColumnRole.NAME)
        other_col = table_mapping.get(ColumnRole.OTHER)
        oneway_col = table_mapping.get(ColumnRole.ONEWAY)
        bridge_col = table_mapping.get(ColumnRole.BRIDGE)
        maxspeed_col = table_mapping.get(ColumnRole.MAX_SPEED)
        maxweight_col = table_mapping.get(ColumnRole.MAX_WEIGHT)
        maxwidth_col = table_mapping.get(ColumnRole.MAX_WIDTH)
        lanes_f_col = table_mapping.get(ColumnRole.LANES_FORWARD)
        lanes_b_col = table_mapping.get(ColumnRole.LANES_BACKWARD)

        missing_roles = []
        if not edge_id_col:
            missing_roles.append(ColumnRole.PRIMARY_KEY.value)
        if not geom_col:
            missing_roles.append(ColumnRole.GEOMETRY.value)
        if not highway_col:
            missing_roles.append(ColumnRole.HIGHWAY.value)
        if not lanes_f_col:
            missing_roles.append(ColumnRole.LANES_FORWARD.value)
        if not lanes_b_col:
            missing_roles.append(ColumnRole.LANES_BACKWARD.value)

        if missing_roles:
            raise TopologyBuildError(
                "Для таблицы '{}' не сопоставлены обязательные поля: {}.".format(
                    line_table, ", ".join(missing_roles)
                )
            )

        qualified_table = self.__qualified_table(line_table)
        edge_id_expr = sql.SQL("l.{}::bigint").format(sql.Identifier(edge_id_col))
        geom_expr = sql.SQL("ST_Transform(l.{}, 4326)").format(sql.Identifier(geom_col))
        highway_expr = sql.SQL("lower(l.{}::text)").format(sql.Identifier(highway_col))
        name_expr = sql.SQL("l.{}").format(sql.Identifier(name_col))
        is_oneway_expr = self.__build_oneway_expr(oneway_col)
        hgv_expr = self.__build_hgv_expr(other_col)
        max_speed_expr = self.__build_max_speed_expr(other_col, plain_column=maxspeed_col)
        max_speed_practical_expr = self.__build_tag_number_expr(other_col, f"{maxspeed_col}:practical")
        max_height_expr = self.__build_max_height_expr(other_col)
        max_width_expr = self.__build_tag_number_expr(other_col, "maxwidth", plain_column=maxwidth_col)
        max_weight_expr = self.__build_tag_number_expr(other_col, "maxweight", plain_column=maxweight_col)
        bridge_expr = self.__build_bridge_expr(other_col, plain_column=bridge_col)
        lanes_forward_expr = self.__build_tag_int_expr(other_col, "lanes:forward", plain_column=lanes_f_col)
        lanes_backward_expr = self.__build_tag_int_expr(other_col, "lanes:backward", plain_column=lanes_b_col)

        query = sql.SQL("""
                WITH
                    inserted_classes AS (
                        INSERT INTO routing.road_classes (class_name)
                            SELECT DISTINCT {highway_expr}
                            FROM {line_table} AS l
                            WHERE {highway_expr} IN (
                                'primary', 'secondary', 'tertiary', 'motorway',
                                'primary_link', 'trunk', 'secondary_link', 'tertiary_link',
                                'motorway_link', 'trunk_link', 'service', 'road', 'unclassified',
                                'residential'
                            )
                        ON CONFLICT (class_name) DO NOTHING
                        RETURNING class_id, class_name
                    ),
                    all_classes AS (
                        SELECT class_id, class_name
                            FROM inserted_classes
                        UNION SELECT class_id, class_name
                            FROM routing.road_classes
                    ),
                    inserted_edges AS (
                        INSERT INTO routing.graph_edges (edge_id, geom)
                            SELECT DISTINCT {edge_id_expr}, {geom_expr}
                            FROM {line_table} AS l
                        INNER JOIN all_classes ac ON {highway_expr} = ac.class_name
                        ON CONFLICT (edge_id) DO NOTHING
                        RETURNING edge_id
                )
                INSERT INTO routing.graph_edge_info (
                    edge_id, road_class_id, name, is_oneway, hgv, bridge,
                    lanes_forward, lanes_backward, max_height, max_width_m,
                    max_weight_t, max_speed_kmh, max_speed_practical_kmh
                )
                    SELECT {edge_id_expr}, ac.class_id, {name_expr},
                    {is_oneway_expr}, {hgv_expr}, {bridge_expr},
                    {lanes_forward_expr}, {lanes_backward_expr}, {max_height_expr},
                    {max_width_expr}, {max_weight_expr}, {max_speed_expr}, {max_speed_practical_expr}
                FROM {line_table} AS l
                    INNER JOIN all_classes ac
                ON {highway_expr} = ac.class_name
                    INNER JOIN inserted_edges ie ON {edge_id_expr} = ie.edge_id;
            """).format(
            edge_id_expr=edge_id_expr,
            geom_expr=geom_expr,
            highway_expr=highway_expr,
            name_expr=name_expr,
            is_oneway_expr=is_oneway_expr,
            max_speed_expr=max_speed_expr,
            max_speed_practical_expr=max_speed_practical_expr,
            max_height_expr=max_height_expr,
            max_width_expr=max_width_expr,
            max_weight_expr=max_weight_expr,
            bridge_expr=bridge_expr,
            lanes_forward_expr=lanes_forward_expr,
            lanes_backward_expr=lanes_backward_expr,
            hgv_expr=hgv_expr,
            line_table=qualified_table
        )

        self.__db.execute_nonquery(query)

    def enrich_edges_from_points(
            self,
            point_layers: list[Layer],
            column_mapping: dict[str, dict[ColumnRole, str | None]] | None = None,
    ):
        """
            Импортирует выбранные точечные объекты как дорожные события и применяет
            штрафы к ближайшим рёбрам без создания новых узлов маршрутизации.
        """
        if not point_layers:
            return

        self.__db.execute_nonquery("TRUNCATE routing.road_point_events RESTART IDENTITY")

        for layer in point_layers:
            table_mapping = column_mapping.get(layer.name, {})
            geom_col = table_mapping.get(ColumnRole.GEOMETRY)
            id_col = table_mapping.get(ColumnRole.PRIMARY_KEY)
            other_col = table_mapping.get(ColumnRole.OTHER)

            if not other_col:
                print(f"Слой '{layer.name}': не задана колонка OTHER_TAGS, точечные события пропущены.")
                continue

            source_id_expr = (
                sql.SQL("p.{}::bigint").format(sql.Identifier(id_col))
                if id_col else sql.SQL("NULL::bigint")
            )
            geom_id = sql.Identifier(geom_col)
            other_id = sql.Identifier(other_col)

            insert_query = sql.SQL("""
                INSERT INTO routing.road_point_events (
                    source_layer, source_id, nearest_edge_id, nearest_node_id,
                    geom, event_type, max_speed_kmh, access, motorcar,
                    traffic_calming, crossing, traffic_signal, tags, cost_penalty
                )
                SELECT
                    {layer_name},
                    {source_id_expr},
                    nearest.edge_id,
                    nearest.node_id,
                    ST_Transform(p.{geom_col}, 4326),
                    CASE
                        WHEN (p.{other_col}::hstore)->'highway' = 'traffic_signals'
                             OR (p.{other_col}::hstore)->'traffic_signals' IS NOT NULL
                            THEN 'traffic_signals'
                        WHEN (p.{other_col}::hstore)->'traffic_calming' IS NOT NULL
                            THEN 'traffic_calming'
                        WHEN (p.{other_col}::hstore)->'maxspeed' IS NOT NULL
                            THEN 'maxspeed'
                        WHEN (p.{other_col}::hstore)->'access' IN ('no', 'private')
                             OR (p.{other_col}::hstore)->'motorcar' IN ('no', 'private')
                            THEN 'access'
                        ELSE COALESCE((p.{other_col}::hstore)->'highway', 'road_point')
                    END,
                    {maxspeed_expr},
                    (p.{other_col}::hstore)->'access',
                    (p.{other_col}::hstore)->'motorcar',
                    (p.{other_col}::hstore)->'traffic_calming',
                    (p.{other_col}::hstore)->'crossing',
                    (
                        (p.{other_col}::hstore)->'highway' = 'traffic_signals'
                        OR (p.{other_col}::hstore)->'traffic_signals' IS NOT NULL
                    ),
                    p.{other_col}::text,
                    CASE
                        WHEN (p.{other_col}::hstore)->'access' IN ('no', 'private')
                             OR (p.{other_col}::hstore)->'motorcar' IN ('no', 'private') THEN -1.0
                        WHEN (p.{other_col}::hstore)->'highway' = 'traffic_signals'
                             OR (p.{other_col}::hstore)->'traffic_signals' IS NOT NULL THEN 25.0
                        WHEN (p.{other_col}::hstore)->'crossing' = 'traffic_lights' THEN 25.0
                        WHEN (p.{other_col}::hstore)->'traffic_calming' IN ('bump', 'table') THEN 30.0
                        WHEN (p.{other_col}::hstore)->'traffic_calming' = 'rumble_strip' THEN 5.0
                        ELSE 0.0
                    END
                FROM {point_table} p
                CROSS JOIN LATERAL (
                    SELECT
                        e.edge_id,
                        CASE
                            WHEN ST_Distance(ST_Transform(p.{geom_col}, 4326)::geography, n_source.geom::geography)
                                 <= ST_Distance(ST_Transform(p.{geom_col}, 4326)::geography, n_target.geom::geography)
                            THEN e.source
                            ELSE e.target
                        END AS node_id
                    FROM routing.graph_edges e
                    LEFT JOIN routing.graph_nodes n_source ON n_source.node_id = e.source
                    LEFT JOIN routing.graph_nodes n_target ON n_target.node_id = e.target
                    ORDER BY e.geom <-> ST_Transform(p.{geom_col}, 4326)
                    LIMIT 1
                ) nearest
                WHERE p.{geom_col} IS NOT NULL;
            """).format(
                layer_name=sql.Literal(layer.name),
                source_id_expr=source_id_expr,
                geom_col=geom_id,
                other_col=other_id,
                point_table=self.__qualified_table(layer.name),
                maxspeed_expr=self.__build_tag_number_expr(other_col, "maxspeed", "p"),
            )

            self.__db.execute_nonquery(insert_query)

        # Обновляем свойства скоростей в таблице graph_edge_info
        self.__db.execute_nonquery("""
            WITH speed_events
                AS (SELECT nearest_edge_id AS edge_id, MIN(max_speed_kmh) AS max_speed_kmh
                    FROM routing.road_point_events
                    WHERE nearest_edge_id IS NOT NULL
                      AND max_speed_kmh IS NOT NULL
                      AND max_speed_kmh > 0
                    GROUP BY nearest_edge_id)
            UPDATE routing.graph_edge_info info
            SET max_speed_kmh = LEAST(COALESCE(info.max_speed_kmh, s.max_speed_kmh), s.max_speed_kmh),
                avg_speed_estimated = LEAST(
                    COALESCE(info.avg_speed_estimated, GREATEST(s.max_speed_kmh * 0.55, 10)),
                    GREATEST(s.max_speed_kmh * 0.55, 10)
                )
            FROM speed_events s
            WHERE info.edge_id = s.edge_id;
            """)

        # Пересчитываем веса в базовой таблице graph_edges
        self.__db.execute_nonquery("""
            UPDATE routing.graph_edges e
            SET cost = e.length_m / (NULLIF(info.avg_speed_estimated, 0) / 3.6),
                reverse_cost = CASE
                    WHEN e.reverse_cost < 0 THEN e.reverse_cost
                    ELSE e.length_m / (NULLIF(info.avg_speed_estimated, 0) / 3.6)
                END
            FROM routing.graph_edge_info info
            WHERE e.edge_id = info.edge_id
             AND info.edge_id IN (SELECT nearest_edge_id
                                  FROM routing.road_point_events
                                  WHERE nearest_edge_id IS NOT NULL);
        """)

        # Наложение штрафов времени на ребра
        self.__db.execute_nonquery("""
            WITH penalties AS (
                SELECT nearest_edge_id AS edge_id,
                MIN(cost_penalty) FILTER (WHERE cost_penalty < 0) AS blocking_penalty,
                SUM(cost_penalty) FILTER (WHERE cost_penalty > 0) AS positive_penalty
                    FROM routing.road_point_events
                    WHERE nearest_edge_id IS NOT NULL
                    GROUP BY nearest_edge_id
            )
            UPDATE routing.graph_edges e
            SET point_cost_penalty = COALESCE(p.blocking_penalty, p.positive_penalty, 0),
            cost = CASE
                WHEN COALESCE(p.blocking_penalty, 0) < 0 THEN -1
                ELSE cost + COALESCE(p.positive_penalty, 0)
            END,
            reverse_cost = CASE
                WHEN reverse_cost < 0 THEN reverse_cost
                WHEN COALESCE(p.blocking_penalty, 0) < 0 THEN -1
                ELSE reverse_cost + COALESCE(p.positive_penalty, 0)
            END
            FROM penalties p
            WHERE e.edge_id = p.edge_id AND COALESCE(p.blocking_penalty, p.positive_penalty, 0) != 0;
        """)

    def create_restrictions_from_pipes(
            self,
            pipe_layers: list[Layer],
            column_mapping: dict[str, dict[ColumnRole, str | None]] | None = None,
    ):
        """ Создаёт габаритные ограничения из надземных трубопроводов """
        if not pipe_layers:
            return

        for layer in pipe_layers:
            table_mapping = column_mapping.get(layer.name, {})
            pipelines_table = self.__qualified_table(layer.name)

            name_col = table_mapping.get(ColumnRole.NAME)
            pipe_height_col = table_mapping.get(ColumnRole.MAX_HEIGHT)
            geom_col = table_mapping.get(ColumnRole.GEOMETRY)
            location_col = table_mapping.get(ColumnRole.LOCATION)

            name_expr = sql.SQL("p.{}").format(sql.Identifier(name_col if name_col else 'Трубопровод'))
            geom_expr = sql.SQL("p.{}").format(sql.Identifier(geom_col))
            location_expr = sql.SQL("p.{}").format(sql.Identifier(location_col))
            pipe_height_expr = sql.SQL("p.{}").format(sql.Identifier(pipe_height_col))

            insert_query = sql.SQL(
                """
                WITH raw_data AS (
                    SELECT DISTINCT ON (n.node_id)
                        {name} AS restriction_name,
                        n.node_id AS node_id,
                        {max_height} AS max_height
                    FROM {pipe_table} p
                        JOIN routing.graph_edges e
                            ON ST_Intersects(ST_Transform({geom_col}, 4326), e.geom)
                        JOIN routing.graph_nodes n ON n.node_id IN (e.source, e.target)
                            AND ST_DWithin(
                                n.geom::geography, ST_ClosestPoint(e.geom, ST_Transform({geom_col}, 4326))::geography, 50
                            )
                    WHERE {location} IN ('overground', 'overhead')
                ),
                inserted_restrictions AS (
                    INSERT INTO routing.restrictions (restriction_id, node_id, restriction_name, user_comment)
                        SELECT
                            (
                                SELECT COALESCE(MAX(restriction_id), 0) FROM routing.restrictions
                            ) + ROW_NUMBER() OVER () AS restriction_id,
                            rd.node_id,
                            rd.restriction_name,
                            rd.restriction_name AS user_comment
                        FROM raw_data rd
                        RETURNING restriction_id, node_id
                )
                INSERT INTO routing.dimension_restrictions (
                    restriction_id,
                    max_height_m,
                    max_width_m,
                    max_depth_m,
                    max_weight_t
                )
                SELECT
                    ir.restriction_id,
                    rd.max_height,
                    0,
                    0,
                    0
                FROM inserted_restrictions ir
                    JOIN raw_data rd ON ir.node_id = rd.node_id;
            """).format(
                pipe_table=pipelines_table,
                name=name_expr,
                geom_col=geom_expr,
                max_height=pipe_height_expr,
                location=location_expr
            )

            self.__db.execute_nonquery(insert_query)

    def create_restrictions_from_roads(self):
        """ Создаёт габаритные ограничения из тегов дорожного слоя """
        self.__db.execute_nonquery(
            """
                WITH
                    raw_roads AS
                    (
                        SELECT e.edge_id,
                            COALESCE(e.target, e.source) AS node_id,
                            COALESCE(info.name, 'Ограничение на дороге') AS name,
                            '' AS comment,
                            NULLIF(info.max_height, 0) AS max_height_m,
                            NULLIF(info.max_width_m, 0) AS max_width_m,
                            NULLIF(info.max_weight_t, 0) AS max_weight_t
                        FROM routing.graph_edges e
                            INNER JOIN routing.graph_edge_info info ON e.edge_id = info.edge_id
                        WHERE COALESCE(e.target, e.source) IS NOT NULL
                        AND (
                            COALESCE(info.max_height, 0) > 0
                            OR COALESCE(info.max_width_m, 0) > 0
                            OR COALESCE(info.max_weight_t, 0) > 0
                        )
                    ),
                ins_base AS
                (
                    INSERT INTO routing.restrictions (
                        restriction_id,
                        restriction_name,
                        node_id,
                        user_comment
                    )
                        SELECT (
                            SELECT COALESCE(MAX(restriction_id), 0)
                            FROM routing.restrictions
                        ) + ROW_NUMBER() OVER (ORDER BY edge_id) AS restriction_id,
                        name,
                        node_id,
                        comment
                    FROM raw_roads
                    ON CONFLICT DO NOTHING
                    RETURNING restriction_id, node_id
                )
                INSERT INTO routing.dimension_restrictions (
                    restriction_id,
                    max_height_m,
                    max_width_m,
                    max_weight_t
                )
                SELECT
                    ib.restriction_id,
                    rr.max_height_m,
                    rr.max_width_m,
                    rr.max_weight_t
                FROM ins_base ib
                INNER JOIN raw_roads rr ON ib.node_id = rr.node_id
            """
        )

    def create_parking_areas(
            self,
            parking_layers: list[Layer],
            column_mapping: dict[str, dict[ColumnRole, str | None]] | None = None,
    ):
        """ Загружает геометрию парковок в routing.parking_areas """
        if not parking_layers:
            return

        self.__db.execute_nonquery("TRUNCATE routing.parking_areas RESTART IDENTITY")

        for layer in parking_layers:
            table_mapping = (column_mapping or {}).get(layer.name, {})
            geom_col = table_mapping.get(ColumnRole.GEOMETRY)
            id_col = table_mapping.get(ColumnRole.PRIMARY_KEY)
            name_col = table_mapping.get(ColumnRole.NAME)
            other_col = table_mapping.get(ColumnRole.OTHER)
            amenity_col = self.__existing_column(layer.name, "amenity")
            parking_col = self.__existing_column(layer.name, "parking")

            source_id_expr = (
                sql.SQL("p.{}::bigint").format(sql.Identifier(id_col))
                if id_col else sql.SQL("NULL::bigint")
            )
            name_expr = (
                sql.SQL("p.{}").format(sql.Identifier(name_col))
                if name_col else sql.SQL("NULL::text")
            )
            amenity_condition = self.__parking_condition("p", amenity_col, parking_col, other_col)

            insert_query = sql.SQL("""
                INSERT INTO routing.parking_areas (source_layer, source_id, name, geom)
                SELECT
                    {layer_name},
                    {source_id_expr},
                    {name_expr},
                    ST_Multi(ST_Transform(p.{geom_col}, 4326))::geometry(MultiPolygon, 4326)
                FROM {parking_table} p
                WHERE p.{geom_col} IS NOT NULL AND {amenity_condition};
            """).format(
                layer_name=sql.Literal(layer.name),
                source_id_expr=source_id_expr,
                name_expr=name_expr,
                geom_col=sql.Identifier(geom_col),
                parking_table=self.__qualified_table(layer.name),
                amenity_condition=amenity_condition,
            )

            self.__db.execute_nonquery(insert_query)

    def __pgr_ksp(self, start_id, end_id, k, profile: VehicleProfile, season_factor: float, route_points=None,
                  restriction_nodes=None):
        """ Используемый алгоритм поиска n маршрутов. """
        sql_edges_query = self.__routing_edges_sql(profile, season_factor, restriction_nodes)
        sql_points_query = self.__routing_points_sql(route_points)

        is_truck = profile.type == VehicleType.TRUCK
        travel_time = self.__travel_time_sql("r.route_length_m", season_factor, is_truck)

        if sql_points_query is None:
            query = f"""
                        WITH routed_edges AS (
                            SELECT
                                r.path_id,
                                r.seq,
                                e.edge_id,
                                CASE 
                                    WHEN r.node = e.source THEN e.geom
                                    ELSE ST_Reverse(e.geom)
                                END AS route_geom,
                                r.cost AS route_cost,
                                r.agg_cost,
                                info.name,
                                info.max_speed_practical_kmh,
                                info.max_speed_kmh,
                                info.avg_speed_estimated,
                                r.node
                            FROM pgr_ksp(%s::text, %s::bigint, %s::bigint, %s::integer, directed := true) AS r
                            JOIN routing.graph_edges AS e ON r.edge = e.edge_id
                            LEFT JOIN routing.graph_edge_info AS info ON e.edge_id = info.edge_id
                        ),
                        route_segments AS (
                            SELECT
                                *,
                                ST_Length(route_geom::geography, true) AS route_length_m
                            FROM routed_edges
                        )
                        SELECT
                            r.path_id,
                            r.edge_id,
                            ST_AsText(r.route_geom) AS geom,
                            {travel_time},
                            r.agg_cost,
                            r.route_length_m,
                            r.name,
                            r.node
                        FROM route_segments AS r
                        ORDER BY r.path_id, r.seq
                    """
            return self.__db.execute_query(query, sql_edges_query, start_id, end_id, k)

        query = f"""
            WITH route_points AS (
                {sql_points_query}
            ),
            raw_route AS (
                SELECT
                    r.*,
                    LEAD(r.node) OVER (PARTITION BY r.path_id ORDER BY r.seq) AS next_node
                FROM pgr_withPointsKSP(
                    %s::text,
                    %s::text,
                    %s::bigint,
                    %s::bigint,
                    %s::integer,
                    'b',
                    directed := true
                ) AS r
            ),
            routed_edges AS (
                SELECT
                    r.path_id,
                    r.seq,
                    e.edge_id,
                    CASE
                        WHEN start_point.pid IS NOT NULL
                             AND end_point.pid IS NOT NULL
                             AND start_point.fraction <= end_point.fraction
                            THEN ST_LineSubstring(e.geom, start_point.fraction, end_point.fraction)
                        WHEN start_point.pid IS NOT NULL
                             AND end_point.pid IS NOT NULL
                            THEN ST_Reverse(ST_LineSubstring(e.geom, end_point.fraction, start_point.fraction))
                        WHEN start_point.pid IS NOT NULL
                             AND r.next_node = e.target
                            THEN ST_LineSubstring(e.geom, start_point.fraction, 1)
                        WHEN start_point.pid IS NOT NULL
                             AND r.next_node = e.source
                            THEN ST_Reverse(ST_LineSubstring(e.geom, 0, start_point.fraction))
                        WHEN end_point.pid IS NOT NULL
                             AND r.node = e.source
                            THEN ST_LineSubstring(e.geom, 0, end_point.fraction)
                        WHEN end_point.pid IS NOT NULL
                             AND r.node = e.target
                            THEN ST_Reverse(ST_LineSubstring(e.geom, end_point.fraction, 1))
                        WHEN r.node = e.source THEN e.geom
                        ELSE ST_Reverse(e.geom)
                    END AS route_geom,
                    r.cost AS route_cost,
                    r.agg_cost,
                    info.name,
                    info.max_speed_practical_kmh,
                    info.max_speed_kmh,
                    info.avg_speed_estimated,
                    r.node
                FROM raw_route AS r
                JOIN routing.graph_edges AS e ON r.edge = e.edge_id
                LEFT JOIN routing.graph_edge_info AS info ON e.edge_id = info.edge_id
                LEFT JOIN route_points AS start_point
                    ON r.node < 0
                    AND start_point.pid = ABS(r.node)
                    AND start_point.edge_id = e.edge_id
                LEFT JOIN route_points AS end_point
                    ON r.next_node < 0
                    AND end_point.pid = ABS(r.next_node)
                    AND end_point.edge_id = e.edge_id
            ),
            route_segments AS (
                SELECT
                    *,
                    ST_Length(route_geom::geography, true) AS route_length_m
                FROM routed_edges
            )
            SELECT
                r.path_id,
                r.edge_id,
                ST_AsText(r.route_geom) AS geom,
                {travel_time},
                r.agg_cost,
                r.route_length_m,
                r.name,
                r.node
            FROM route_segments AS r
            ORDER BY r.path_id, r.seq
            """
        return self.__db.execute_query(query, sql_edges_query, sql_points_query, start_id, end_id, k)

    def get_routes(
            self,
            profile,
            start_id: int,
            end_id: int,
            waypoint_ids: list[int] = None,
            route_points: list = None,
            restriction_nodes: list[int] = None,
            season_factor: float = 1,
            routes_n: int = 3) -> list[list[dict]] | None:
        """ Находит пути из start_id в end_id с учётом промежуточных точек """
        routing_point_ids = self.__routing_point_ids(start_id, end_id, waypoint_ids, route_points)
        routing_start_id = routing_point_ids[0]
        routing_end_id = routing_point_ids[-1]
        routing_waypoint_ids = routing_point_ids[1:-1]

        for point_id in routing_point_ids:
            if point_id >= 0 and not self.__check_point(point_id):
                raise NodeNotFoundError(f"Узел {point_id} не найден в БД!")
        if not routing_waypoint_ids:
            rows = self.__pgr_ksp(
                routing_start_id, routing_end_id, routes_n, profile, season_factor, route_points, restriction_nodes
            )
            routes = {}
            for row in rows:
                path_id = row[0]
                if path_id not in routes:
                    routes[path_id] = []
                routes[path_id].append({
                    "edge_id": row[1],
                    "geom": row[2],
                    "cost": row[3],
                    "agg_cost": row[4],
                    "length_m": row[5],
                    "name": row[6],
                    "node": row[7]
                })
        else:
            route_point_ids = [routing_start_id] + routing_waypoint_ids + [routing_end_id]
            segments = []

            # Собираем k-альтернатив для каждого сегмента отдельно
            for i in range(len(route_point_ids) - 1):
                seg_start, seg_end = route_point_ids[i], route_point_ids[i + 1]
                seg_rows = self.__pgr_ksp(
                    seg_start, seg_end, routes_n, profile, season_factor, route_points, restriction_nodes
                )

                # Группируем ребра по path_id внутри текущего сегмента
                seg_routes = {}
                for row in seg_rows:
                    path_id = row[0]
                    if path_id not in seg_routes:
                        seg_routes[path_id] = []
                    seg_routes[path_id].append({
                        "edge_id": row[1],
                        "geom": row[2],
                        "cost": row[3],
                        "agg_cost": row[4],
                        "length_m": row[5],
                        "name": row[6],
                        "node": row[7]
                    })

                # Если какое-то плечо вообще не построилось, сквозной маршрут невозможен
                if not seg_routes:
                    return None
                segments.append(seg_routes)

            # Валидация стыков и сборка сквозных маршрутов
            from collections import deque
            queue = deque()

            for path_id, edges in segments[0].items():
                if edges:
                    # узел, в который пришло последнее ребро сегмента
                    last_geom = edges[-1]["geom"]
                    queue.append((1, [path_id], last_geom))

            valid_combinations = []

            while queue:
                seg_idx, chosen_paths, prev_last_geom = queue.popleft()

                # Если дошли до конца всех сегментов — комбинация валидна
                if seg_idx == len(segments):
                    valid_combinations.append(chosen_paths)
                    if len(valid_combinations) >= routes_n:  # Ограничиваем лимит сквозных путей
                        break
                    continue

                current_segment = segments[seg_idx]

                # Перебираем альтернативы текущего сегмента и проверяем стык с предыдущим
                for path_id, edges in current_segment.items():
                    if not edges:
                        continue

                    first_geom = edges[0]["geom"]

                    # Конец последнего ребра предыдущего сегмента должен совпадать с началом первого ребра текущего
                    prev_end_point = prev_last_geom.split(',')[-1].strip().replace('LINESTRING(', '').replace(')', '')
                    curr_start_point = first_geom.split(',')[0].strip().replace('LINESTRING(', '').replace(')', '')
                    if prev_end_point == curr_start_point:
                        next_last_geom = edges[-1]["geom"]
                        queue.append((seg_idx + 1, chosen_paths + [path_id], next_last_geom))

            # Сборка результатов по цепочкам
            routes = {}
            for idx, path_combo in enumerate(valid_combinations, start=1):
                combined_path = []
                current_agg_cost = 0.0
                for seg_idx, path_id in enumerate(path_combo):
                    segment_edges = segments[seg_idx][path_id]
                    for edge in segment_edges:
                        edge_copy = edge.copy()
                        current_agg_cost += edge_copy["cost"]
                        edge_copy["agg_cost"] = current_agg_cost
                        combined_path.append(edge_copy)
                routes[idx] = combined_path
        return list(routes.values())

    def __routing_edges_sql(
            self,
            profile: VehicleProfile,
            season_factor: float,
            restriction_nodes: list = None,
    ) -> str:
        restriction_condition = ""
        if restriction_nodes:
            ids = ",".join(map(str, restriction_nodes))
            restriction_condition = f"""
            AND e.source NOT IN ({ids})
            AND e.target NOT IN ({ids})
            """

        is_truck = profile.type == VehicleType.TRUCK
        cost_expr = self.__route_cost_expr("e.cost", is_truck, season_factor)
        reverse_cost_expr = self.__route_cost_expr("e.reverse_cost", is_truck, season_factor)

        return f"""
            SELECT e.edge_id as id, e.source, e.target,
            CASE
                WHEN info.max_height IS NOT NULL AND info.max_height < {profile.height} THEN -1
                WHEN info.max_width_m IS NOT NULL AND info.max_width_m > 0 AND info.max_width_m < {profile.width} THEN -1
                WHEN info.max_weight_t IS NOT NULL AND info.max_weight_t > 0 AND info.max_weight_t < {profile.weight} THEN -1
                ELSE {cost_expr}
            END as cost,
            CASE
                WHEN info.max_height IS NOT NULL AND info.max_height < {profile.height} THEN -1
                WHEN info.max_width_m IS NOT NULL AND info.max_width_m > 0 AND info.max_width_m < {profile.width} THEN -1
                WHEN info.max_weight_t IS NOT NULL AND info.max_weight_t > 0 AND info.max_weight_t < {profile.weight} THEN -1
                WHEN info.is_oneway = TRUE THEN -1
                ELSE {reverse_cost_expr}
            END as reverse_cost
            FROM routing.graph_edges e
            INNER JOIN routing.graph_edge_info info ON e.edge_id = info.edge_id
                {"WHERE info.hgv IS NOT FALSE" if profile.type == VehicleType.TRUCK else "WHERE 1=1"}
                {restriction_condition}
        """

    def __routing_points_sql(self, route_points):
        if not route_points:
            return None

        select_statements = []
        for index, point in enumerate(route_points, start=1):
            if point.edge_id is None or point.fraction is None:
                continue
            fraction = min(max(float(point.fraction), 0.000001), 0.999999)

            select_statements.append(
                f"""SELECT
                    {index}::int4 AS pid,
                    {int(point.edge_id)}::int8 AS edge_id,
                    {fraction}::float8 AS fraction
                """
            )

        if not select_statements:
            return None

        return " UNION ALL ".join(select_statements)

    def __routing_point_ids(
            self,
            start_id: int,
            end_id: int,
            waypoint_ids: list[int] | None,
            route_points: list | None,
    ) -> list[int]:
        fallback_ids = [start_id] + list(waypoint_ids or []) + [end_id]
        if not route_points:
            return fallback_ids

        routing_ids = []
        for index, point in enumerate(route_points, start=1):
            if point.edge_id is not None and point.fraction is not None:
                routing_ids.append(-index)
            else:
                fallback_index = index - 1
                routing_ids.append(fallback_ids[fallback_index] if fallback_index < len(fallback_ids) else point.node_id)

        return routing_ids if len(routing_ids) >= 2 else fallback_ids

    def __check_point(self, point_id: int) -> bool:
        result = self.__db.execute_query(
            "SELECT node_id FROM routing.graph_nodes WHERE node_id = %s",
            point_id
        )
        return bool(result)

    def find_nearest_edge(self, x: float, y: float, max_distance_m: float = 50.0) -> dict | None:
        result = self.__db.execute_query("""
            SELECT
                edge_id,
                source,
                target,
                ST_X(ST_ClosestPoint(geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326))) AS snapped_x,
                ST_Y(ST_ClosestPoint(geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326))) AS snapped_y,
                ST_LineLocatePoint(geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) AS fraction,
                ST_Distance(
                    geom::geography,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                ) AS distance
            FROM routing.graph_edges
            WHERE ST_DWithin(
                geom::geography,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s
            )
            AND source IS NOT NULL
            AND target IS NOT NULL
            ORDER BY distance
            LIMIT 1
        """, x, y, x, y, x, y, x, y, x, y, max_distance_m)

        if not result:
            return None
        row = result[0]
        return {
            "edge_id": row[0],
            "source": row[1],
            "target": row[2],
            "snapped_x": row[3],
            "snapped_y": row[4],
            "fraction": row[5],
            "distance": row[6],
        }

    def get_first_point_source_coordinates(
            self,
            layers: list[Layer],
            column_mapping: dict[str, dict[ColumnRole, str | None]] | None = None,
    ) -> tuple[float, float] | None:
        point_layer = self.__get_point_table(layers)
        if point_layer is None:
            return None

        mapping = (column_mapping or {}).get(point_layer.name, {})
        geom_col = mapping.get(ColumnRole.GEOMETRY) or "geom"
        id_col = mapping.get(ColumnRole.PRIMARY_KEY)

        order_clause = (
            sql.SQL("ORDER BY {} ASC").format(sql.Identifier(id_col))
            if id_col else sql.SQL("")
        )

        query = sql.SQL("""
            SELECT
                ST_X(ST_Transform({geom_col}, 4326)) AS lon,
                ST_Y(ST_Transform({geom_col}, 4326)) AS lat
            FROM {point_table}
            WHERE {geom_col} IS NOT NULL
            {order_clause}
            LIMIT 1
        """).format(
            geom_col=sql.Identifier(geom_col),
            point_table=self.__qualified_table(point_layer.name),
            order_clause=order_clause,
        )

        result = self.__db.execute_query(query)
        if not result:
            return None

        lon, lat = result[0]
        if lon is None or lat is None:
            return None
        return float(lon), float(lat)

    def __route_cost_expr(self, default_column: str, is_truck: bool, season_factor: float) -> str:
        vehicle_factor = 1 if not is_truck else 0.75
        speed_expr = f"COALESCE(info.max_speed_kmh, info.avg_speed_estimated, info.max_speed_practical_kmh)"
        effective_speed = f"{speed_expr} * {season_factor} * {vehicle_factor}"
        cost = f"length_m / ({effective_speed} / 3.6)"

        return f"CASE WHEN {default_column} < 0 THEN -1 ELSE {cost} END"

    def __travel_time_sql(self, length_expr: str, season_factor: float, is_truck: bool) -> str:
        vehicle_factor = 0.75 if is_truck else 1.0
        speed_expr = (
            "COALESCE("
            "r.max_speed_practical_kmh, "
            "r.max_speed_kmh, "
            "r.avg_speed_estimated, "
            "30"
            ")"
        )
        effective_speed_kmh = f"GREATEST(({speed_expr}) * {season_factor} * {vehicle_factor}, 1)"
        return f"{length_expr} / ({effective_speed_kmh} / 3.6) AS cost"

    def get_node_coordinates(self, node_id: int) -> tuple[float, float] | None:
        result = self.__db.execute_query(
            "SELECT x, y FROM routing.graph_nodes WHERE node_id = %s",
            node_id
        )
        if result and len(result) > 0:
            return float(result[0][0]), float(result[0][1])
        return None

    def __get_line_table(self, layers: list[Layer]) -> str | None:
        for layer in layers:
            if layer.role is LayerRole.ROADS:
                return layer.name
        return None

    def __get_layers_by_role(self, layers: list[Layer], role: LayerRole) -> list[Layer]:
        return [layer for layer in layers if layer.role is role]

    def __get_point_table(self, layers: list[Layer]) -> Layer | None:
        for layer in layers:
            if layer.role is LayerRole.POINTS:
                return layer
        return None

    def __table_parts(self, table_name: str) -> tuple[str | None, str]:
        if "." in table_name:
            schema_name, plain_table_name = table_name.split(".", 1)
            return schema_name, plain_table_name
        return self.__db.schema, table_name

    def __existing_column(self, table_name: str, column_name: str) -> str | None:
        schema_name, plain_table_name = self.__table_parts(table_name)
        if not schema_name:
            query = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s AND lower(column_name) = lower(%s)
                LIMIT 1
            """
            rows = self.__db.execute_query(query, plain_table_name, column_name)
        else:
            query = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = %s
                  AND table_name = %s
                  AND lower(column_name) = lower(%s)
                LIMIT 1
            """
            rows = self.__db.execute_query(query, schema_name, plain_table_name, column_name)
        return rows[0][0] if rows else None

    def __first_existing_column(self, table_name: str, column_names: tuple[str, ...]) -> str | None:
        for column_name in column_names:
            existing = self.__existing_column(table_name, column_name)
            if existing:
                return existing
        return None

    def __find_table(self, table_name: str) -> str | None:
        schema_name, plain_table_name = self.__table_parts(table_name)
        if schema_name:
            rows = self.__db.execute_query(
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                  AND lower(table_name) = lower(%s)
                LIMIT 1
                """,
                schema_name,
                plain_table_name,
            )
        else:
            rows = self.__db.execute_query(
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE lower(table_name) = lower(%s)
                ORDER BY CASE WHEN table_schema = 'public' THEN 0 ELSE 1 END
                LIMIT 1
                """,
                plain_table_name,
            )
        if not rows:
            return None
        found_schema, found_table = rows[0]
        return f"{found_schema}.{found_table}"

    def __qualified_table(self, table_name: str):
        if "." in table_name:
            schema_name, plain_table_name = table_name.split(".", 1)
            return sql.SQL("{}.{}").format(
                sql.Identifier(schema_name),
                sql.Identifier(plain_table_name),
            )
        if self.__db.schema:
            return sql.SQL("{}.{}").format(
                sql.Identifier(self.__db.schema),
                sql.Identifier(table_name),
            )
        return sql.Identifier(table_name)

    def __build_oneway_expr(self, plain_column: str):
        checks = []
        if plain_column:
            checks.append(sql.SQL("lower(l.{}::text) IN ('yes', '1', 'true')").format(sql.Identifier(plain_column)))
        if not checks:
            return sql.SQL("FALSE")
        condition = checks[0]
        for check in checks[1:]:
            condition = sql.SQL("({} OR {})").format(condition, check)
        return sql.SQL("CASE WHEN {} THEN TRUE ELSE FALSE END").format(condition)

    def __build_hgv_expr(self, other_col: str | None):
        if not other_col:
            return sql.SQL("NULL::boolean")
        return sql.SQL("""
            CASE
                WHEN (l.{0}::hstore)->'hgv' IN ('yes', 'designated') THEN TRUE
                WHEN (l.{0}::hstore)->'hgv' IN ('no') THEN FALSE
                ELSE NULL
            END
        """).format(sql.Identifier(other_col))

    def __build_max_height_expr(self, other_col: str | None):
        return self.__build_tag_number_expr(other_col, "maxheight")

    def __build_max_speed_expr(self, other_col: str | None, plain_column: str | None = None):
        return self.__build_tag_number_expr(other_col, "maxspeed", plain_column=plain_column)

    def __build_bridge_expr(self, other_col: str | None, plain_column: str | None = None):
        return self.__tag_in_condition(
            "l",
            plain_column,
            other_col,
            "bridge",
            ("yes", "true", "1", "viaduct"),
        )

    def __build_tag_number_expr(
            self,
            other_col: str | None,
            tag_name: str,
            alias: str = "l",
            plain_column: str | None = None,
    ):
        expressions = []
        if plain_column:
            expressions.append(self.__number_from_column(alias, plain_column))
        if other_col:
            expressions.append(sql.SQL("""
                NULLIF(
                    regexp_replace(
                        replace(({}.{})::hstore->{}, ',', '.'),
                        '[^0-9.]',
                        '',
                        'g'
                    ),
                    ''
                )::double precision
            """).format(
                sql.Identifier(alias),
                sql.Identifier(other_col),
                sql.Literal(tag_name),
            ))
        if not expressions:
            return sql.SQL("NULL::double precision")
        if len(expressions) == 1:
            return expressions[0]
        return sql.SQL("COALESCE({})").format(sql.SQL(", ").join(expressions))

    def __build_tag_int_expr(
            self,
            other_col: str | None,
            tag_name: str,
            alias: str = "l",
            plain_column: str | None = None
    ):
        if not other_col:
            return sql.SQL("NULL::integer")
        number_expr = self.__build_tag_number_expr(other_col, tag_name, alias, plain_column)
        return sql.SQL("({})::integer").format(number_expr)

    def __number_from_column(self, alias: str, plain_column: str):
        return sql.SQL("""
            NULLIF(
                regexp_replace(
                    replace({}.{}::text, ',', '.'),
                    '[^0-9.]',
                    '',
                    'g'
                ),
                ''
            )::double precision
        """).format(sql.Identifier(alias), sql.Identifier(plain_column))

    def __tag_in_condition(
            self,
            alias: str,
            plain_column: str | None,
            other_col: str | None,
            tag_name: str,
            tag_values: tuple[str, ...],
    ):
        parts = []
        values = sql.SQL(", ").join(sql.Literal(value) for value in tag_values)
        if plain_column:
            parts.append(
                sql.SQL("lower({}.{}::text) IN ({})").format(
                    sql.Identifier(alias),
                    sql.Identifier(plain_column),
                    values,
                )
            )
        if other_col:
            parts.append(
                sql.SQL("lower(({}.{}::hstore)->{}) IN ({})").format(
                    sql.Identifier(alias),
                    sql.Identifier(other_col),
                    sql.Literal(tag_name),
                    values,
                )
            )
        if not parts:
            return sql.SQL("FALSE")
        condition = parts[0]
        for part in parts[1:]:
            condition = sql.SQL("({} OR {})").format(condition, part)
        return condition

    def __parking_condition(
            self,
            alias: str,
            amenity_col: str | None,
            parking_col: str | None,
            other_col: str | None,
    ):
        parts = []
        if parking_col:
            parts.append(sql.SQL("{}.{} IS NOT NULL").format(sql.Identifier(alias), sql.Identifier(parking_col)))
        if amenity_col or other_col:
            parts.append(self.__tag_equals_condition(alias, amenity_col, other_col, "amenity", "parking"))
        if not parts:
            return sql.SQL("TRUE")
        condition = parts[0]
        for part in parts[1:]:
            condition = sql.SQL("({} OR {})").format(condition, part)
        return condition

    def __tag_equals_condition(
            self,
            alias: str,
            plain_column: str | None,
            other_col: str | None,
            tag_name: str,
            tag_value: str,
    ):
        parts = []
        if plain_column:
            parts.append(
                sql.SQL("{}.{} = {}").format(
                    sql.Identifier(alias),
                    sql.Identifier(plain_column),
                    sql.Literal(tag_value),
                )
            )
        if other_col:
            parts.append(
                sql.SQL("({}.{}::hstore)->{} = {}").format(
                    sql.Identifier(alias),
                    sql.Identifier(other_col),
                    sql.Literal(tag_name),
                    sql.Literal(tag_value),
                )
            )
        if not parts:
            return sql.SQL("FALSE")
        condition = parts[0]
        for part in parts[1:]:
            condition = sql.SQL("({} OR {})").format(condition, part)
        return condition

    def __tag_text_select_expr(
            self,
            alias: str,
            plain_column: str | None,
            other_col: str | None,
            tag_name: str,
    ):
        expressions = []
        if plain_column:
            expressions.append(
                sql.SQL("{}.{}").format(sql.Identifier(alias), sql.Identifier(plain_column))
            )
        if other_col:
            expressions.append(
                sql.SQL("({}.{}::hstore)->{}").format(
                    sql.Identifier(alias),
                    sql.Identifier(other_col),
                    sql.Literal(tag_name),
                )
            )
        if not expressions:
            return sql.SQL("NULL::text")
        if len(expressions) == 1:
            return expressions[0]
        return sql.SQL("COALESCE({}, {})").format(expressions[0], expressions[1])
