# -*- coding: utf-8 -*-
from qgis.PyQt import QtCore, QtWidgets
from qgis.PyQt.QtWidgets import QMessageBox

from qgis_route_planner.models.column_role import ColumnRole
from qgis_route_planner.views.base_qdialog import BaseQDialog


class TableColumnsConfigDialog(BaseQDialog):
    """Диалоговое окно для сопоставления полей таблиц и их атрибутов"""
    def __init__(self, parent=None, selected_layers=None, table_columns=None):
        super().__init__(parent)
        self.__initialization_completed = False
        self.selected_layers = selected_layers
        self.__table_columns = table_columns
        self.__mapped_columns = None

        self.setupUi()
        self.__init_mapping_table()

    def setupUi(self):
        self.setObjectName("TableColumnsDialog")
        self.resize(1000, 700)

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")

        self.label = QtWidgets.QLabel(self)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)

        self.tableWidget = QtWidgets.QTableWidget(self)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.verticalLayout.addWidget(self.tableWidget)

        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())
        self.buttonBox.setSizePolicy(sizePolicy)
        self.buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel |
                                          QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi()
        self.buttonBox.accepted.connect(self.__on_accept_button_click)
        self.buttonBox.rejected.connect(self.__on_reject_button_click)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("TableColumnsDialog", "Шаг 3: сопоставление полей выбранных таблиц"))
        self.label.setText(_translate("TableColumnsDialog", "Укажите назначение каждого из столбцов для таблиц."))

    def closeEvent(self, event):
        if not self.__initialization_completed:
            close_question = QMessageBox.question(
                self,
                "Внимание",
                "Для продолжения требуется выполнить настройку полей.\nВы уверены, что хотите закрыть мастер подключения?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if close_question == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()

    def __init_mapping_table(self):
        row_count = len([e.value for e in ColumnRole])
        col_count = len(self.selected_layers)

        self.tableWidget.setRowCount(row_count)
        self.tableWidget.setColumnCount(col_count)

        for index, layer in enumerate(self.selected_layers):
            self.tableWidget.setHorizontalHeaderItem(
                index,
                QtWidgets.QTableWidgetItem(layer[0])
            )

        for index, role in enumerate(ColumnRole):
            self.tableWidget.setVerticalHeaderItem(
                index,
                QtWidgets.QTableWidgetItem(role.value)
            )

        for i in range(0, row_count):
            for j in range(0, col_count):
                table_name = self.selected_layers[j][0]
                role = list(ColumnRole)[i]
                self.tableWidget.setCellWidget(i, j, self.__create_cell_combobox(table_name, role))

    def __create_cell_combobox(self, table_name: str, role: ColumnRole):
        colTypeComboBox = QtWidgets.QComboBox()
        colTypeComboBox.setObjectName("colTypeComboBox")
        colTypeComboBox.addItem("-- Не задано --", None)

        columns = self.__table_columns.get(table_name, [])
        preferred_column = self.__guess_column_for_role(role, columns)

        for column in columns:
            column_name, column_type = self.__normalize_column_info(column)
            if not column_name:
                continue

            label = column_name
            if column_type:
                label = f"{column_name} ({column_type})"

            colTypeComboBox.addItem(label, column_name)

            if preferred_column and column_name.lower() == preferred_column.lower():
                colTypeComboBox.setCurrentIndex(colTypeComboBox.count() - 1)

        return colTypeComboBox

    def __normalize_column_info(self, column):
        if isinstance(column, str):
            return column, None

        if isinstance(column, dict):
            return column.get("column_name") or column.get("name"), column.get("data_type") or column.get("type")

        if isinstance(column, (tuple, list)) and column:
            column_name = column[0]
            column_type = column[1] if len(column) > 1 else None
            return column_name, column_type

        return None, None

    def __guess_column_for_role(self, role: ColumnRole, columns) -> str | None:
        """Попытка предугадать назначение поля по названию"""
        candidates_by_role = {
            ColumnRole.PRIMARY_KEY: ("osm_id", "id", "gid", "fid", "objectid"),
            ColumnRole.GEOMETRY: ("geom", "geometry", "wkb_geometry", "the_geom"),
            ColumnRole.HIGHWAY: ("highway",),
            ColumnRole.WATERWAY: ("waterway",),
            ColumnRole.AERIALWAY: ("aerialway",),
            ColumnRole.RAILWAY: ("railway",),
            ColumnRole.MAN_MADE: ("man_made",),
            ColumnRole.BARRIER: ("barrier",),
            ColumnRole.NAME: ("name",),
            ColumnRole.ADDRESS: ("addr:full", "address", "addr_street", "addr:street"),
            ColumnRole.IS_IN: ("is_in",),
            ColumnRole.Z_ORDER: ("z_order", "zorder"),
            ColumnRole.REF: ("ref",),
            ColumnRole.OTHER: ("other_tags", "tags"),
        }

        available_columns = []
        for column in columns:
            column_name, _ = self.__normalize_column_info(column)
            if column_name:
                available_columns.append(column_name)

        available_by_lower = {column_name.lower(): column_name for column_name in available_columns}
        for candidate in candidates_by_role.get(role, ()):
            matched_column = available_by_lower.get(candidate.lower())
            if matched_column:
                return matched_column

        return None

    def __on_accept_button_click(self):
        self.__mapped_columns = self.get_mapped_columns()
        self.__initialization_completed = True
        self.accept()

    def __on_reject_button_click(self):
        self.close()

    def get_mapped_columns(self) -> dict[str, dict[ColumnRole, str | None]]:
        result = {}

        for col_idx, (table_name, _) in enumerate(self.selected_layers):
            result[table_name] = {}

            for row_idx, role in enumerate(ColumnRole):
                combo = self.tableWidget.cellWidget(row_idx, col_idx)
                if combo is None:
                    result[table_name][role] = None
                    continue

                result[table_name][role] = combo.currentData()

        return result

    @property
    def mapped_columns(self):
        return self.__mapped_columns
