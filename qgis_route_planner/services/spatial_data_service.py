from qgis.core import QgsDataSourceUri, QgsVectorLayer

from ..data.models.layer_config_model import Layer
from ..repositories import RoadGraphRepository, LayerRepository, VehicleProfileRepository
from ..repositories import RestrictionRepository


class SpatialDataService:
    """Сервис доступа к табличным слоям БД"""

    def __init__(
        self,
        layer_repo: LayerRepository,
        graph_repo: RoadGraphRepository,
        vehicle_repo: VehicleProfileRepository,
        restriction_repo: RestrictionRepository | None = None,
    ):
        self.__graph_repo: RoadGraphRepository = graph_repo
        self.__layer_repo: LayerRepository = layer_repo
        self.__vehicle_repo: VehicleProfileRepository = vehicle_repo
        self.__restriction_repo: RestrictionRepository | None = restriction_repo

    def get_spatial_layers(self, schema: str = "public") -> list[QgsVectorLayer]:
        """Возвращает пространственные слои из схемы"""
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

    def get_schemas(self) -> list[str]:
        tuple_list = self.__layer_repo.get_all_schemas()
        return [item[0] for item in tuple_list]

    def get_tables(self, schema: str) -> list[str]:
        tuple_list = self.__layer_repo.get_all_tables(schema)
        return [item[0] for item in tuple_list]

    def get_table_columns(self, table_name: str) -> list[str]:
        tuple_list = self.__layer_repo.get_table_columns(table_name)
        return [item[0] for item in tuple_list]

    def run_init_database(self, layers: list[Layer], column_mapping=None):
        """Инициализация БД"""
        try:
            self.__graph_repo.create_tables(layers, column_mapping)

            self.__vehicle_repo.create_tables()

            if self.__restriction_repo is not None:
                self.__restriction_repo.ensure_default_types()

        except Exception as e:
            raise e