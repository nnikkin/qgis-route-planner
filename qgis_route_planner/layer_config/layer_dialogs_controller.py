from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from layer_config_model import LayerConfigModel
    from qgis_route_planner.layer_config.cols_config_model import ColumnsConfigModel
    from spatial_data_service import SpatialDataService

from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot

from qgis_route_planner.layer_config.column_role import ColumnRole
from layer_role import LayerRole


class LayerDialogsController:
    """ Контроллер окон инициализации плагина """
    layers_selected = pyqtSignal()
    columns_configured = pyqtSignal()

    connection_failed = pyqtSignal(str)
    layer_selection_failed = pyqtSignal(str)
    column_config_failed = pyqtSignal(str)
    init_cancelled = pyqtSignal()

    show_error = pyqtSignal(str)
    show_warning = pyqtSignal(str)
    show_info = pyqtSignal(str)

    def __init__(
            self,
            layer_config_model: LayerConfigModel,
            columns_config_model: ColumnsConfigModel,
            service: SpatialDataService = None,
    ):
        super().__init__()

        self.__layer_config_model: LayerConfigModel = layer_config_model
        self.__columns_config_model: ColumnsConfigModel = columns_config_model

        self.__service = service
        self.__schema: str = ""

    def set_schema(self, schema: str):
        self.__schema = schema

    def set_service(self, service: SpatialDataService):
        self.__service = service


# для SelectLayersDialog
    @pyqtSlot()
    def get_layers(self) -> list[str]:
        if self.__service is None:
            self.layer_selection_failed.emit("Не удалось подключиться.\nВернитесь к настройке подключения.")
            return []

        if not self.__schema:
            self.layer_selection_failed.emit("Не выбрана схема базы данных.")
            return []

        return self.__service.get_tables(self.__schema)

    @pyqtSlot(str, object, object)
    def add_layer_to_config(self, layer_name: str, layer_role: LayerRole):
        self.__layer_config_model.add_layer(layer_name, layer_role)

    @pyqtSlot(int)
    def remove_layer_from_config(self, index: int):
        if 0 <= index < len(self.__layer_config_model.selected_layers):
            self.__layer_config_model.pop_layer(index)

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

        if not any(l.role == LayerRole.ROADS for l in self.__layer_config_model.selected_layers):
            self.layer_selection_failed.emit("Для построения графа необходим хотя бы один слой с ролью 'Слой дорог'.")
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
        errors = self.__columns_config_model.validate_required_mappings()
        if errors:
            self.column_config_failed.emit(
                "Для следующих из выбранных слоёв необходимо сопоставить обязательные поля:\n"
                + "\n- ".join(errors)
            )
            return

        self.columns_configured.emit()
