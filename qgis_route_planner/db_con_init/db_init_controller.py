from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .db_config_model import DbConfigModel

from qgis.PyQt.QtCore import pyqtSignal, pyqtSlot, QObject

class DbInitController(QObject):
    """ Контроллер окон инициализации плагина """

    con_test_requested = pyqtSignal(str, str, str, str, str)
    con_params_obtained = pyqtSignal()

    connection_failed = pyqtSignal(str)
    layer_selection_failed = pyqtSignal(str)
    column_config_failed = pyqtSignal(str)
    initialization_cancelled = pyqtSignal()

    show_error = pyqtSignal(str)
    show_warning = pyqtSignal(str)
    show_info = pyqtSignal(str)

    def __init__(self, model: DbConfigModel):
        super().__init__()
        self.__db_config_model: DbConfigModel = model

    def cancel_initialization(self):
        self.initialization_cancelled.emit()

    def request_connection_test(self):
        self.con_test_requested.emit(
            self.__db_config_model.host,
            self.__db_config_model.port,
            self.__db_config_model.username,
            self.__db_config_model.password,
            self.__db_config_model.database
        )

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

    def validate_values_for_schema(self):
        return self.__db_config_model.validate_values_for_schema()

    def validate_connection_step(self):
        return self.__db_config_model.validate_all_values()

    def connection_step_finish(self):
        self.con_params_obtained.emit()