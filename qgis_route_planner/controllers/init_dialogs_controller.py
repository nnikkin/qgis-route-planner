from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot, QObject

from ..data.models import DbConfigModel, LayerConfigModel, ColumnsConfigModel
from ..utils import ColumnRole, GeometryType, LayerRole
from ..services import SpatialDataService


class InitDialogsController(QObject):
    con_test_requested = pyqtSignal()
    con_params_obtained = pyqtSignal()
    layers_selected = pyqtSignal()
    columns_configured = pyqtSignal()
    schemas_loaded = pyqtSignal(list)

    connection_failed = pyqtSignal(str)
    layer_selection_failed = pyqtSignal(str)
    column_config_failed = pyqtSignal(str)
    init_cancelled = pyqtSignal()

    def __init__(
            self,
            db_config_model: DbConfigModel,
            layer_config_model: LayerConfigModel,
            columns_config_model: ColumnsConfigModel,
            service: SpatialDataService = None,
    ):
        super().__init__()

        self.__db_config_model: DbConfigModel = db_config_model
        self.__layer_config_model: LayerConfigModel = layer_config_model
        self.__columns_config_model: ColumnsConfigModel = columns_config_model

        self.__service = service

    def set_service(self, service: SpatialDataService):
        self.__service = service

    @pyqtSlot()
    def initialization_cancelled(self):
        self.init_cancelled.emit()

    @pyqtSlot()
    def request_connection(self):
        self.__service = None
        self.con_test_requested.emit()

    def __create_connection(self):
        self.con_test_requested.emit()
        print(
            self.__db_config_model.host,
            self.__db_config_model.port,
            self.__db_config_model.username,
            self.__db_config_model.password,
            self.__db_config_model.database
        )


# для DbConnectionSetupDialog
    @pyqtSlot(str)
    def change_host_value(self, new_value: str):
        self.__db_config_model.host = new_value

    @pyqtSlot(str)
    def change_port_value(self, new_value: str):
        self.__db_config_model.port = new_value

    @pyqtSlot(str)
    def change_username_value(self, new_value: str):
        self.__db_config_model.username = new_value

    @pyqtSlot(str)
    def change_password_value(self, new_value: str):
        self.__db_config_model.password = new_value

    @pyqtSlot(str)
    def change_database_value(self, new_value: str):
        self.__db_config_model.database = new_value

    @pyqtSlot(str)
    def change_schema_value(self, new_value: str):
        self.__db_config_model.schema = new_value

    @pyqtSlot()
    def validate_values_for_schema(self):
        return self.__db_config_model.validate_values_for_schema()

    @pyqtSlot()
    def validate_connection_step(self):
        return self.__db_config_model.validate_all_values()

    @pyqtSlot()
    def get_schemas(self) -> list[str]:
        if self.__service is None:
            self.connection_failed.emit("Не удалось подключиться.\nПроверьте правильность введённых данных.")
            return []
        return self.__service.get_schemas()

    @pyqtSlot()
    def connection_step_finish(self):
        self.con_params_obtained.emit()


# для SelectLayersDialog
    @pyqtSlot()
    def get_layers(self) -> list[str]:
        return self.__service.get_tables(self.__db_config_model.schema)

    @pyqtSlot(str, object, object)
    def add_layer_to_config(self, layer_name: str, geom_type: GeometryType, layer_role: LayerRole):
        self.__layer_config_model.add_layer(layer_name, geom_type, layer_role)

    @pyqtSlot(int)
    def remove_layer_from_config(self, index: int):
        if 0 <= index < len(self.__layer_config_model.selected_layers):
            self.__layer_config_model.pop_layer(index)

    @pyqtSlot(int, object)
    def change_geometry_type(self, index: int, new_type: GeometryType):
        layer = self.__layer_config_model.selected_layers[index]
        layer.geom_type = new_type
        self.__layer_config_model.update_layer(layer, index)

    @pyqtSlot(int, object)
    def change_layer_role(self, index: int, new_role: LayerRole):
        layer = self.__layer_config_model.selected_layers[index]
        layer.role = new_role
        self.__layer_config_model.update_layer(layer, index)

    @pyqtSlot()
    def layer_select_step_finish(self):
        if not self.__layer_config_model.selected_layers:
            self.layer_selection_failed.emit("Выберите слои.")
            return

        if not self.__layer_config_model.check_for_linestring():
            self.layer_selection_failed.emit("Для продолжения необходим хотя бы один слой с геометрией LineString.")
            return

        selected_layers = self.__layer_config_model.selected_layers
        self.__columns_config_model.set_layers(selected_layers)

        for layer in selected_layers:
            columns = self.__service.get_table_columns(layer.name)
            self.__columns_config_model.set_available_columns(layer.name, columns)

        self.layers_selected.emit()

# для TableColumnsConfigDialog
    @pyqtSlot()
    def change_column_info(self, table_name: str, col_name: str | None, role: ColumnRole):
        self.__columns_config_model.set_mapping(table_name, role, col_name)

    @pyqtSlot()
    def column_setup_step_finish(self):
        is_valid, errors = self.__columns_config_model.validate_required_mappings()
        if not is_valid:
            self.column_config_failed.emit(
                "Для линейных слоёв необходимо сопоставить обязательные поля:\n"
                + "\n".join(errors)
            )
            return

        self.columns_configured.emit()
