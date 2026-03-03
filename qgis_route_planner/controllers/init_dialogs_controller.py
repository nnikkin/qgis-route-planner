from qgis_route_planner.repositories.db_connection import DbConnection
from qgis_route_planner.services.database_service import DatabaseService
from qgis_route_planner.views.table_cols_view import TableColumnsConfigDialog
from qgis_route_planner.views.select_layers_view import *
from qgis_route_planner.views.dbcon_setup_view import DbConnectionSetupDialog

from qgis.PyQt.QtWidgets import QMessageBox, QDialog
from qgis.PyQt.QtCore import pyqtSignal, QObject

class InitDialogsController(QObject):
    """Контроллер окон инициализации модуля (DbConnectionSetupDialog и SelectLayersDialog)"""

    # Сигналы
    db_connection_created = pyqtSignal(DbConnection)
    db_connection_test = pyqtSignal(DbConnection)
    layers_selected = pyqtSignal(list)
    initialization_finished = pyqtSignal(list, dict)
    init_cancelled = pyqtSignal()

    def __init__(self, db_service: DatabaseService = None):
        super().__init__()

        self.__db_connection: DbConnection = None
        self.__selected_layers: list[tuple[str, GeometryType]] = list()

        self.__db_service = db_service

        self.__db_init_view = DbConnectionSetupDialog()
        self.__layer_select_view = SelectLayersDialog()
        self.__table_cols_view = None

        self.__connect_signals()

    def __connect_signals(self):
        self.__db_init_view.host_edit.textChanged.connect(self.__on_text_changed)
        self.__db_init_view.database_edit.textChanged.connect(self.__on_text_changed)
        self.__db_init_view.port_edit.textChanged.connect(self.__on_text_changed)
        self.__db_init_view.username_edit.textChanged.connect(self.__on_text_changed)
        self.__db_init_view.password_edit.textChanged.connect(self.__on_text_changed)
        self.__db_init_view.check_con_button.clicked.connect(self.__on_check_button_click)

        self.__db_init_view.buttonBox.accepted.connect(self.__on_accept_button_click_dbview)
        self.__layer_select_view.buttonBox.accepted.connect(self.__on_accept_button_click_layerview)
        self.__db_init_view.buttonBox.rejected.connect(lambda: self.__on_reject_button_click(self.__db_init_view))
        self.__layer_select_view.buttonBox.rejected.connect(lambda: self.__on_reject_button_click(self.__layer_select_view))

    def set_db_service(self, db_service: DatabaseService):
        self.__db_service = db_service

    def __on_text_changed(self):
        host_value = self.__db_init_view.host_edit.text()
        port_value = self.__db_init_view.port_edit.text()
        username_value = self.__db_init_view.username_edit.text()
        password_value = self.__db_init_view.password_edit.text()
        database_value = self.__db_init_view.database_edit.text()

        are_fields_filled = all(x for x in (host_value, port_value, database_value, username_value,password_value))

        self.__db_init_view.check_con_button.setEnabled(are_fields_filled)

        self.__db_init_view.schema_comboBox.clear()
        self.__db_init_view.schema_comboBox.setEnabled(False)

    def __on_check_button_click(self):
        self.__db_init_view.schema_comboBox.setEnabled(False)

        self.__db_connection = DbConnection(
            host=self.__db_init_view.host_edit.text(),
            database=self.__db_init_view.database_edit.text(),
            port=self.__db_init_view.port_edit.text(),
            username=self.__db_init_view.username_edit.text(),
            password=self.__db_init_view.password_edit.text()
        )

        if self.__db_connection.test_connection():
            self.db_connection_test.emit(self.__db_connection)
        else:
            QMessageBox.critical(
                self.__db_init_view,
                "Ошибка",
                "Не удалось подключиться к базе данных.\nПроверьте правильность введённых данных.",
                QMessageBox.Ok,
            )
            return


    def fill_schema_combobox(self):
        schemas = self.__db_service.get_all_schemas()
        self.__db_init_view.schema_comboBox.clear()
        self.__db_init_view.schema_comboBox.addItems([i[0] for i in schemas])
        self.__db_init_view.schema_comboBox.setEnabled(True)

    def start_init_process(self):
        self.__db_init_view.exec()

    def __on_accept_button_click_dbview(self):
        selected_schema = self.__db_init_view.schema_comboBox.currentText()
        self.__db_connection = DbConnection(
            host=self.__db_init_view.host_edit.text(),
            database=self.__db_init_view.database_edit.text(),
            port=self.__db_init_view.port_edit.text(),
            username=self.__db_init_view.username_edit.text(),
            password=self.__db_init_view.password_edit.text(),
            schema=selected_schema
        )

        if not self.__db_connection.has_required_params():
            QMessageBox.information(
                self.__db_init_view,
                "",
                "Заполните все поля, затем нажмите \"Проверить подключение\" и выберите схему из списка.",
                QMessageBox.Ok,
            )
            return

        self.db_connection_created.emit(self.__db_connection)

        # следующий шаг настройки
        # получаем все таблицы по схеме
        tables_list = self.__db_service.get_all_tables(self.__db_connection.schema)

        if len(tables_list) == 0:
            QMessageBox.warning(
                self.__db_init_view,
                "",
                "В выбранной схеме отсутствуют таблицы."
            )
            return

        table_names = [row[0] for row in tables_list]
        self.__layer_select_view.fill_list(table_names)

        self.__db_init_view.hide()
        self.__show_layer_select_dialog()

    def __on_accept_button_click_layerview(self):
        selected_layers = self.__layer_select_view.get_table_rows()

        has_linestring = any(layer_type == GeometryType.LINESTRING for _, layer_type in selected_layers)

        if not has_linestring:
            QMessageBox.warning(
                self.__layer_select_view,
                "",
                "Для продолжения необходимо выбрать хотя бы одну таблицу с геометрией типа LineString.",
                QMessageBox.Ok,
            )
            return

        self.__selected_layers = selected_layers
        self.layers_selected.emit(self.__selected_layers)
        self.__show_table_columns_dialog()

    def __show_table_columns_dialog(self):
        table_columns = {}

        try:
            for table_name, _ in self.__selected_layers:
                table_columns[table_name] = self.__db_service.get_table_columns(table_name)
        except Exception as e:
            QMessageBox.critical(
                self.__layer_select_view,
                "Ошибка",
                f"Не удалось получить список столбцов выбранных таблиц:\n{e}",
                QMessageBox.Ok,
            )
            return

        self.__layer_select_view.initialization_completed = True
        self.__layer_select_view.hide()

        self.__table_cols_view = TableColumnsConfigDialog(
            selected_layers=self.__selected_layers,
            table_columns=table_columns,
        )
        self.__table_cols_view.buttonBox.accepted.connect(self.__on_accept_button_click_tablecols_view)
        self.__table_cols_view.buttonBox.rejected.connect(lambda: self.__on_reject_button_click(self.__table_cols_view))
        self.__table_cols_view.exec()

    def __show_layer_select_dialog(self):
        self.__layer_select_view.exec()

    def __on_accept_button_click_tablecols_view(self):
        mapped_columns = self.__table_cols_view.mapped_columns
        if mapped_columns is None:
            mapped_columns = self.__table_cols_view.get_mapped_columns()

        self.__table_cols_view.close()
        self.initialization_finished.emit(self.__selected_layers, mapped_columns)

    def __on_reject_button_click(self, parent):
        parent.close()
        self.init_cancelled.emit()
