from __future__ import annotations

from psycopg import sql

from ..data.models.layer_config_model import Layer
from ..utils import ColumnRole, GeometryType
from ..data.vehicle import VehicleProfile
from ..repositories import DbConnection, LayerRepository

class RoadGraphRepository:
    def __init__(self, db: DbConnection, layer_repository: LayerRepository):
        self.__db = db
        self.__layer_repository = layer_repository

    def __create_edges_table(self):
        try:
            self.__db.execute_nonquery("""
                CREATE TABLE IF NOT EXISTS routing.graph_edges (
                    edge_id BIGINT PRIMARY KEY,
                    source BIGINT REFERENCES routing.graph_nodes(node_id),
                    x1 DOUBLE PRECISION,
                    y1 DOUBLE PRECISION,
                    target BIGINT REFERENCES routing.graph_nodes(node_id),
                    x2 DOUBLE PRECISION,
                    y2 DOUBLE PRECISION,
                    geom GEOMETRY(LineString, 4326),
                    length_m DOUBLE PRECISION,
                    cost DOUBLE PRECISION,
                    reverse_cost DOUBLE PRECISION,
                    road_class_id SMALLINT REFERENCES routing.road_classes(class_id),
                    name TEXT,
                    is_oneway BOOLEAN,
                    hgv BOOLEAN,
                    max_height FLOAT,
                    avg_speed_estimated DOUBLE PRECISION,
                    max_speed_kmh DOUBLE PRECISION
                );
            """)
        except Exception as e:
            print(e)

    def __create_nodes_table(self):
        try:
            self.__db.execute_nonquery("""
                CREATE TABLE IF NOT EXISTS routing.graph_nodes (
                    node_id BIGINT PRIMARY KEY,
                    in_edges BIGINT[],
                    out_edges BIGINT[],
                    x DOUBLE PRECISION,
                    y DOUBLE PRECISION,
                    geom GEOMETRY(Point, 4326),
                    -- атрибуты, обогащённые из слоя точек
                    access TEXT DEFAULT NULL,
                    motorcar TEXT DEFAULT NULL,
                    traffic_calming TEXT DEFAULT NULL,
                    crossing TEXT DEFAULT NULL,
                    traffic_sign TEXT DEFAULT NULL,
                    node_cost_penalty DOUBLE PRECISION DEFAULT 0.0
                );
            """)
        except Exception as e:
            print(e)

    def __create_road_class_table(self):
        try:
            self.__db.execute_nonquery("""
                CREATE TABLE IF NOT EXISTS routing.road_classes (
                    class_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    class_name VARCHAR(20) UNIQUE NOT NULL
                );
            """)
        except Exception as e:
            print(e)


    def __fill_edges_source_target(self):
        try:
            self.__db.execute_nonquery("""
                UPDATE routing.graph_edges AS e
                SET source = v.node_id, x1 = v.x, y1 = v.y
                FROM routing.graph_nodes AS v
                WHERE ST_StartPoint(e.geom) = v.geom;
             """)

            self.__db.execute_nonquery("""
                UPDATE routing.graph_edges AS e
                SET target = v.node_id, x2 = v.x, y2 = v.y
                FROM routing.graph_nodes AS v
                WHERE ST_EndPoint(e.geom) = v.geom;
            """)
        except Exception as e:
            print(e)

    def __extract_vertices(self):
        try:
            self.__db.execute_nonquery("""
                INSERT INTO routing.graph_nodes (node_id, in_edges, out_edges, x, y, geom)
                SELECT id, in_edges, out_edges, x, y, geom
                FROM pgr_extractVertices(
                    'SELECT edge_id as id, geom FROM routing.graph_edges ORDER BY edge_id'
                )
                ON CONFLICT (node_id) DO NOTHING;
            """)
        except Exception as e:
            print(e)

    def __remove_orphan_nodes(self):
        try:
            self.__db.execute_nonquery("""
                DELETE FROM routing.graph_nodes n
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM routing.graph_edges e
                        WHERE e.source = n.node_id OR e.target = n.node_id
                    );
            """)
        except Exception as e:
            print(e)

    def __fill_edges_cost(self):
        try:
            self.__db.execute_nonquery("""
                UPDATE routing.graph_edges
                SET
                    length_m = ST_Length(geom::geography, true),
                    cost = ST_Length(geom::geography, true) / (NULLIF(max_speed_kmh, 0) / 3.6),
                    reverse_cost = CASE
                        WHEN is_oneway = TRUE THEN -1
                        ELSE ST_Length(geom::geography, true) / (NULLIF(max_speed_kmh, 0) / 3.6)
                    END;
            """)
        except Exception as e:
            print(e)

    def __fill_avg_speed(self):
        try:
            self.__db.execute_nonquery("""
                UPDATE routing.graph_edges e
                SET avg_speed_estimated = CASE
                    WHEN e.max_speed_kmh > 0 THEN e.max_speed_kmh * 0.8
                    WHEN c.class_name = 'motorway' THEN 100
                    WHEN c.class_name = 'primary' THEN 60
                    WHEN c.class_name = 'service' THEN 20
                    ELSE 40
                END
                FROM routing.road_classes c
                WHERE e.road_class_id = c.class_id
            """)
        except Exception as e:
            print(e)

    def __create_indexes(self):
        try:
            self.__db.execute_nonquery("""
                CREATE INDEX IF NOT EXISTS idx_graph_edges_geom
                ON routing.graph_edges USING GIST (geom);
            """)
            self.__db.execute_nonquery("""
                CREATE INDEX IF NOT EXISTS idx_graph_nodes_geom
                ON routing.graph_nodes USING GIST (geom);
            """)
        except Exception as e:
            print(e)

    def __keep_largest_connected_components(self):
        try:
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
        except Exception as e:
            print(e)

    def create_topology(self):
        """Пересчитать топологию существующего графа"""
        table_exists = self.__db.execute_query("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'graph_edges' AND table_schema = 'routing'
            );
        """)

        if not table_exists:
            raise BaseException("Таблица graph_edges не найдена. Сначала загрузите данные!")
        else:
            count = self.__db.execute_query("SELECT COUNT(*) FROM routing.graph_edges;")
            if count and count[0][0] == 0:
                raise BaseException("Нет данных в таблице graph_edges. Сначала загрузите данные!")

        self.__fill_edges_source_target()
        self.__keep_largest_connected_components()
        self.__remove_orphan_nodes()
        self.__fill_avg_speed()
        self.__fill_edges_cost()

    def create_tables(
            self,
            layers: list[Layer],
            column_mapping: dict[str, dict[ColumnRole, str | None]] | None = None,
    ):
        """Создание таблиц и заполнение графа из слоёв дорог"""
        try:
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
            self.__insert_edges_from_mapping(layers, column_mapping)

            count = self.__db.execute_query("SELECT COUNT(*) FROM routing.graph_nodes;")[0][0]
            if count == 0:
                self.__extract_vertices()

            self.__create_indexes()
            self.create_topology()
        except Exception as e:
            raise RuntimeError(f"Произошла ошибка во время создания таблиц: {e}")


    def __insert_edges_from_mapping(
            self,
            layers: list[Layer],
            column_mapping: dict[str, dict[ColumnRole, str | None]] | None,
    ):
        line_table = self.__get_line_table(layers)
        if line_table is None:
            raise ValueError("Не выбрана таблица с линейной геометрией для построения графа.")

        self.__db.execute_nonquery("TRUNCATE routing.graph_edges CASCADE")
        self.__db.execute_nonquery("TRUNCATE routing.graph_nodes CASCADE")
        self.__db.execute_nonquery("TRUNCATE routing.road_classes CASCADE")

        table_mapping = (column_mapping or {}).get(line_table, {})
        edge_id_col = table_mapping.get(ColumnRole.PRIMARY_KEY)
        geom_col = table_mapping.get(ColumnRole.GEOMETRY)
        highway_col = table_mapping.get(ColumnRole.HIGHWAY)
        name_col = table_mapping.get(ColumnRole.NAME)
        other_col = table_mapping.get(ColumnRole.OTHER)

        missing_roles = []
        if not edge_id_col:
            missing_roles.append(ColumnRole.PRIMARY_KEY.value)
        if not geom_col:
            missing_roles.append(ColumnRole.GEOMETRY.value)
        if not highway_col:
            missing_roles.append(ColumnRole.HIGHWAY.value)

        if missing_roles:
            raise ValueError(
                "Для таблицы '{}' не сопоставлены обязательные поля: {}.".format(
                    line_table, ", ".join(missing_roles)
                )
            )

        qualified_table = self.__qualified_table(line_table)
        edge_id_expr = sql.SQL("l.{}::bigint").format(sql.Identifier(edge_id_col))
        geom_expr = sql.SQL("ST_Transform(l.{}, 4326)").format(sql.Identifier(geom_col))
        highway_expr = sql.SQL("l.{}").format(sql.Identifier(highway_col))
        name_expr = (
            sql.SQL("l.{}").format(sql.Identifier(name_col))
            if name_col else sql.SQL("NULL::text")
        )
        is_oneway_expr = self.__build_oneway_expr(other_col)
        hgv_expr = self.__build_hgv_expr(other_col)
        max_speed_expr = self.__build_max_speed_expr(other_col)
        max_height_expr = self.__build_max_height_expr(other_col)

        query = sql.SQL("""
            WITH inserted_classes AS (
                INSERT INTO routing.road_classes (class_name)
                SELECT DISTINCT {highway_expr}
                FROM {line_table} AS l
                WHERE {highway_expr} IN (
                    'primary', 'secondary', 'tertiary', 'motorway',
                    'primary_link', 'trunk', 'secondary_link', 'tertiary_link',
                    'motorway_link', 'trunk_link', 'service', 'road', 'unclassified'
                )
                ON CONFLICT (class_name) DO NOTHING
                RETURNING class_id, class_name
            ),
            all_classes AS (
                SELECT class_id, class_name FROM inserted_classes
                UNION
                SELECT class_id, class_name FROM routing.road_classes
            )
            INSERT INTO routing.graph_edges (
                edge_id, geom, road_class_id, name, is_oneway,
                max_speed_kmh, max_height, hgv
            )
            SELECT
                {edge_id_expr},
                {geom_expr},
                ac.class_id,
                {name_expr},
                {is_oneway_expr},
                {max_speed_expr},
                {max_height_expr},
                {hgv_expr}
            FROM {line_table} AS l
            INNER JOIN all_classes ac ON {highway_expr} = ac.class_name
            ON CONFLICT (edge_id) DO NOTHING;
        """).format(
            edge_id_expr=edge_id_expr,
            geom_expr=geom_expr,
            highway_expr=highway_expr,
            name_expr=name_expr,
            is_oneway_expr=is_oneway_expr,
            max_speed_expr=max_speed_expr,
            max_height_expr=max_height_expr,
            hgv_expr=hgv_expr,
            line_table=qualified_table
        )

        try:
            self.__db.execute_nonquery(query)
        except Exception as e:
            print(e)


    def enrich_nodes_from_points(
            self,
            point_layers: list[Layer],
            column_mapping: dict[str, dict[ColumnRole, str | None]] | None = None,
    ):
        """
        Обогащает узлы графа атрибутами из слоёв точек через пространственный join.

        Теги, которые извлекаются из other_tags (hstore):
          - access / motorcar:          блокировка узла
          - traffic_calming:            штраф к стоимости (bump/table: +30s, rumble_strip: +5s)
          - crossing=traffic_lights:    штраф +25s
          - traffic_sign:               сохраняется как мета-информация
        """
        if not point_layers:
            return

        for col, typ in [
            ("access", "TEXT"),
            ("motorcar", "TEXT"),
            ("traffic_calming", "TEXT"),
            ("crossing", "TEXT"),
            ("traffic_sign", "TEXT"),
            ("node_cost_penalty", "DOUBLE PRECISION"),
        ]:
            try:
                self.__db.execute_nonquery(
                    f"ALTER TABLE routing.graph_nodes ADD COLUMN IF NOT EXISTS {col} {typ} DEFAULT NULL;"
                )
            except Exception:
                pass

        for layer in point_layers:
            table_mapping = (column_mapping or {}).get(layer.name, {})
            geom_col = table_mapping.get(ColumnRole.GEOMETRY) or "geom"
            other_col = table_mapping.get(ColumnRole.OTHER)

            if not other_col:
                print(f"[enrich_nodes] Слой '{layer.name}': не задана колонка OTHER_TAGS, пропускаем.")
                continue

            qualified_table = self.__qualified_table(layer.name)
            geom_id = sql.Identifier(geom_col)
            other_id = sql.Identifier(other_col)

            # Радиус сопоставления узла с точкой — 10 м
            enrich_query = sql.SQL("""
                UPDATE routing.graph_nodes n
                SET
                    access          = p_data.access,
                    motorcar        = p_data.motorcar,
                    traffic_calming = p_data.traffic_calming,
                    crossing        = p_data.crossing,
                    traffic_sign    = p_data.traffic_sign,
                    node_cost_penalty = p_data.penalty
                FROM (
                    SELECT DISTINCT ON (n2.node_id)
                        n2.node_id,
                        (p.{other_col}::hstore)->'access'          AS access,
                        (p.{other_col}::hstore)->'motorcar'         AS motorcar,
                        (p.{other_col}::hstore)->'traffic_calming'  AS traffic_calming,
                        (p.{other_col}::hstore)->'crossing'         AS crossing,
                        (p.{other_col}::hstore)->'traffic_sign'     AS traffic_sign,
                        CASE
                            WHEN (p.{other_col}::hstore)->'access'   IN ('no', 'private')  THEN -1.0
                            WHEN (p.{other_col}::hstore)->'motorcar' IN ('no', 'private')  THEN -1.0
                            WHEN (p.{other_col}::hstore)->'crossing' = 'traffic_lights'    THEN 25.0
                            WHEN (p.{other_col}::hstore)->'traffic_calming' IN ('bump', 'table') THEN 30.0
                            WHEN (p.{other_col}::hstore)->'traffic_calming' = 'rumble_strip'     THEN 5.0
                            ELSE 0.0
                        END AS penalty
                    FROM {point_table} p
                    JOIN routing.graph_nodes n2
                        ON ST_DWithin(
                            ST_Transform(p.{geom_col}, 4326)::geography,
                            n2.geom::geography,
                            10
                        )
                    ORDER BY n2.node_id, ST_Distance(p.{geom_col}, n2.geom)
                ) p_data
                WHERE n.node_id = p_data.node_id;
            """).format(
                other_col=other_id,
                geom_col=geom_id,
                point_table=qualified_table,
            )

            try:
                self.__db.execute_nonquery(enrich_query)
            except Exception as e:
                print(f"[enrich_nodes] Ошибка при обогащении из слоя '{layer.name}': {e}")

        try:
            self.__db.execute_nonquery("""
                UPDATE routing.graph_edges e
                SET
                    cost         = CASE
                        WHEN n.node_cost_penalty < 0 THEN -1
                        ELSE cost + n.node_cost_penalty
                    END,
                    reverse_cost = CASE
                        WHEN n.node_cost_penalty < 0 THEN -1
                        ELSE reverse_cost + n.node_cost_penalty
                    END
                FROM routing.graph_nodes n
                WHERE e.target = n.node_id
                  AND (n.node_cost_penalty IS NOT NULL AND n.node_cost_penalty != 0);
            """)
        except Exception as e:
            print(f"[enrich_nodes] Ошибка при применении штрафов: {e}")


    def create_restrictions_from_pipes(
            self,
            pipe_layers: list[Layer],
            column_mapping: dict[str, dict[ColumnRole, str | None]] | None = None,
    ):
        """
        Создаёт ограничения на узлах графа, которые пересекаются с трубопроводами.

        Логика: если ребро дороги пересекает трубопровод, находим ближайший узел
        к месту пересечения и добавляем запись в routing.restrictions с типом
        'piping' (type_id=4 — добавляем при необходимости).
        Эти ограничения затем учитываются при маршрутизации как закрытые узлы
        (через restriction_nodes в pgr_ksp).
        """
        if not pipe_layers:
            return

        try:
            self.__db.execute_nonquery("""
                INSERT INTO routing.restriction_types (restriction_type_id, code, name)
                VALUES (4, 'piping', 'Трубопровод')
                ON CONFLICT (restriction_type_id) DO NOTHING;
            """)
        except Exception as e:
            print(f"[pipes] Не удалось добавить тип ограничения: {e}")
            return

        for layer in pipe_layers:
            table_mapping = (column_mapping or {}).get(layer.name, {})
            geom_col = table_mapping.get(ColumnRole.GEOMETRY) or "geom"
            name_col = table_mapping.get(ColumnRole.NAME)

            qualified_table = self.__qualified_table(layer.name)
            geom_id = sql.Identifier(geom_col)
            name_expr = (
                sql.SQL("p.{}").format(sql.Identifier(name_col))
                if name_col else sql.SQL("'Трубопровод'")
            )

            # Находим узлы, ближайшие к пересечениям дорог с трубопроводами
            insert_query = sql.SQL("""
                INSERT INTO routing.restrictions (
                    restriction_id,
                    restriction_type_id,
                    name,
                    node_id,
                    value_num,
                    value_text
                )
                SELECT
                    COALESCE(MAX(r.restriction_id), 0) + ROW_NUMBER() OVER () AS restriction_id,
                    4 AS restriction_type_id,
                    {name_expr} AS name,
                    n.node_id,
                    NULL,
                    'auto:piping' AS value_text
                FROM {pipe_table} p
                JOIN routing.graph_edges e
                    ON ST_Intersects(
                        ST_Transform(p.{geom_col}, 4326),
                        e.geom
                    )
                JOIN routing.graph_nodes n
                    ON n.node_id IN (e.source, e.target)
                    AND ST_DWithin(
                        n.geom::geography,
                        ST_ClosestPoint(
                            e.geom,
                            ST_Transform(p.{geom_col}, 4326)
                        )::geography,
                        50
                    )
                CROSS JOIN (SELECT COALESCE(MAX(restriction_id), 0) AS max_id FROM routing.restrictions) r
                WHERE NOT EXISTS (
                    SELECT 1 FROM routing.restrictions ex
                    WHERE ex.node_id = n.node_id AND ex.value_text = 'auto:piping'
                )
                ON CONFLICT DO NOTHING;
            """).format(
                name_expr=name_expr,
                geom_col=geom_id,
                pipe_table=qualified_table,
            )

            try:
                self.__db.execute_nonquery(insert_query)
            except Exception as e:
                print(f"[pipes] Ошибка при создании ограничений из '{layer.name}': {e}")


    def __pgr_ksp(
            self,
            start_id: int,
            end_id: int,
            k: int,
            profile: VehicleProfile,
            restriction_nodes: list = None):

        restriction_condition = ""
        if restriction_nodes:
            ids = ",".join(map(str, restriction_nodes))
            restriction_condition = f"""
            AND source NOT IN ({ids})
            AND target NOT IN ({ids})
            """

        sql_inner_query = f"""
            SELECT edge_id as id, source, target,
                   CASE
                       WHEN max_height IS NOT NULL AND max_height < {profile.height_m} THEN -1
                       ELSE cost
                   END as cost,
                   CASE
                       WHEN max_height IS NOT NULL AND max_height < {profile.height_m} THEN -1
                       ELSE reverse_cost
                   END as reverse_cost
            FROM routing.graph_edges
            {"WHERE hgv IS NOT FALSE" if profile.type.lower() == 'truck' else "WHERE 1=1"}
            {restriction_condition}
        """
        return self.__db.execute_query(
            """
            SELECT
                r.path_id,
                e.edge_id,
                ST_AsText(e.geom) AS geom,
                r.cost,
                r.agg_cost,
                e.length_m
            FROM pgr_ksp(
                %s::text,
                %s::bigint,
                %s::bigint,
                %s::integer,
                directed := true
            ) AS r
            JOIN routing.graph_edges AS e ON r.edge = e.edge_id
            ORDER BY r.path_id, r.seq
            """,
            sql_inner_query, start_id, end_id, k
        )

    def get_routes(
            self,
            start_id: int,
            end_id: int,
            profile: VehicleProfile,
            waypoint_ids: list[int] = None,
            restriction_nodes: list[int] = None,
            routes_n: int = 3) -> list[list[dict]] | None:
        """Находит пути из start_id в end_id с учётом промежуточных точек."""
        if not self.__check_point(start_id):
            raise BaseException(f"Стартовый узел {start_id} не найден в БД!")

        if not self.__check_point(end_id):
            raise BaseException(f"Конечный узел {end_id} не найден в БД!")

        try:
            if not waypoint_ids:
                rows = self.__pgr_ksp(start_id, end_id, routes_n, profile, restriction_nodes)
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
                        "length_m": row[5]
                    })
            else:
                route_point_ids = [start_id] + waypoint_ids + [end_id]
                segments = []
                for i in range(len(route_point_ids) - 1):
                    seg_start, seg_end = route_point_ids[i], route_point_ids[i + 1]
                    seg_rows = self.__pgr_ksp(seg_start, seg_end, routes_n, profile)
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
                            "length_m": row[5]
                        })
                    segments.append(seg_routes)

                routes = {}
                for path_id in range(routes_n):
                    combined = []
                    for seg_routes in segments:
                        best_key = path_id if path_id in seg_routes else 0
                        combined.extend(seg_routes.get(best_key, []))
                    if combined:
                        routes[path_id] = combined

            return list(routes.values())

        except Exception as e:
            import traceback
            print(e)
            print(traceback.format_exc())
            return None

    def __check_point(self, point_id: int) -> bool:
        try:
            result = self.__db.execute_query(
                "SELECT node_id FROM routing.graph_nodes WHERE node_id = %s",
                point_id
            )
            return bool(result)
        except Exception as e:
            print(e)
            return False

    def find_nearest_node(self, x: float, y: float, max_distance_m: float = 10.0) -> tuple | None:
        result = self.__db.execute_query("""
            SELECT node_id,
                   ST_Distance(
                       geom::geography,
                       ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                   ) as distance
            FROM routing.graph_nodes
            WHERE ST_DWithin(
                geom::geography,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s
            )
            ORDER BY distance
            LIMIT 1
        """, x, y, x, y, max_distance_m)
        return result[0] if result else None

    def is_point_on_road_network(self, x: float, y: float, max_distance_m: float = 50.0) -> bool:
        return self.find_nearest_edge(x, y, max_distance_m) is not None

    def find_nearest_edge(self, x: float, y: float, max_distance_m: float = 50.0) -> dict | None:
        result = self.__db.execute_query("""
            SELECT
                edge_id,
                source,
                target,
                ST_X(ST_ClosestPoint(geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326))) AS snapped_x,
                ST_Y(ST_ClosestPoint(geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326))) AS snapped_y,
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
            ORDER BY distance
            LIMIT 1
        """, x, y, x, y, x, y, x, y, max_distance_m)

        if not result:
            return None
        row = result[0]
        return {
            "edge_id": row[0],
            "source": row[1],
            "target": row[2],
            "snapped_x": row[3],
            "snapped_y": row[4],
            "distance": row[5],
        }

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
            if layer.geom_type is GeometryType.LINESTRING:
                return layer.name
        return None

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

    def __build_oneway_expr(self, other_col: str | None):
        if not other_col:
            return sql.SQL("FALSE")
        return sql.SQL("""
            CASE
                WHEN (l.{}::hstore)->'oneway' IN ('yes', '1', 'true') THEN TRUE
                ELSE FALSE
            END
        """).format(sql.Identifier(other_col))

    def __build_hgv_expr(self, other_col: str | None):
        if not other_col:
            return sql.SQL("FALSE")
        return sql.SQL("""
            CASE
                WHEN (l.{0}::hstore)->'hgv' IN ('yes', 'designated') THEN TRUE
                WHEN (l.{0}::hstore)->'hgv' IN ('no') THEN FALSE
                ELSE NULL
            END
        """).format(sql.Identifier(other_col))

    def __build_max_height_expr(self, other_col: str | None):
        if not other_col:
            return sql.SQL("null")
        return sql.SQL("""
            COALESCE(
                NULLIF(regexp_replace((l.{}::hstore)->'maxheight', '[^0-9]', '', 'g'), '')::double precision,
                60
            )
        """).format(sql.Identifier(other_col))

    def __build_max_speed_expr(self, other_col: str | None):
        if not other_col:
            return sql.SQL("60::double precision")
        return sql.SQL("""
            COALESCE(
                NULLIF(regexp_replace((l.{}::hstore)->'maxspeed', '[^0-9]', '', 'g'), '')::double precision,
                60
            )
        """).format(sql.Identifier(other_col))