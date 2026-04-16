from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from db_config_model import DbConfigModel
    from schema_service import SchemaService

from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot

class DbInitController:
    """ Контроллер окон инициализации плагина """

    con_test_requested = pyqtSignal()
    con_params_obtained = pyqtSignal()
    schemas_loaded = pyqtSignal(list)

    connection_failed = pyqtSignal(str)
    layer_selection_failed = pyqtSignal(str)
    column_config_failed = pyqtSignal(str)
    init_cancelled = pyqtSignal()

    show_error = pyqtSignal(str)
    show_warning = pyqtSignal(str)
    show_info = pyqtSignal(str)

    def __init__(
            self,
            db_config_model: DbConfigModel,
            service: SchemaService = None,
    ):
        super().__init__()

        self.__db_config_model: DbConfigModel = db_config_model

        self.__service = service

    def set_service(self, service: SchemaService):
        self.__service = service

    @pyqtSlot()
    def initialization_cancelled(self):
        self.init_cancelled.emit()

    @pyqtSlot()
    def request_connection(self):
        self.__service = None
        self.con_test_requested.emit()

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