from qgis.core import QgsDataSourceUri, QgsVectorLayer

from qgis_route_planner.models.geometry_types import GeometryType
from qgis_route_planner.repositories.graph_repository import RoadGraphRepository
from qgis_route_planner.repositories.layer_repository import LayerRepository
from qgis_route_planner.repositories.vehicle_repository import VehicleProfileRepository


class DatabaseService:
    """Cервис доступа к табличным слоям БД"""

    def __init__(self, layer_repo: LayerRepository, graph_repo: RoadGraphRepository, vehicle_repo: VehicleProfileRepository):
        self.__graph_repo: RoadGraphRepository = graph_repo
        self.__layer_repo: LayerRepository = layer_repo
        self.__vehicle_repo: VehicleProfileRepository = vehicle_repo

    def load_all_spatial_layers(self, schema: str = "public") -> list[QgsVectorLayer]:
        """Возвращает пространственные слои из схемы."""
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
        except Exception as e:
            print(f"Error loading spatial layers: {e}")
            return []

    def get_all_schemas(self) -> list[tuple]:
        return self.__layer_repo.get_all_schemas()

    def get_all_tables(self, schema: str) -> list[tuple]:
        return self.__layer_repo.get_all_tables(schema)

    def get_table_columns(self, table_name: str) -> list[tuple]:
        return self.__layer_repo.get_table_columns(table_name)

    def run_init_database(self, layers: list[tuple[str, GeometryType]], column_mapping=None):
        """Инициализация БД"""
        self.__graph_repo.create_tables(layers, column_mapping)
        self.__vehicle_repo.create_tables()
