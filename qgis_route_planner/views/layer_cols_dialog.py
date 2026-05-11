# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..controllers import InitDialogsController
    from ..data.models import ColumnsConfigModel
    from ..data.models.cols_config_model import ColumnInfo

from qgis.PyQt import QtCore, QtWidgets
from qgis.PyQt.QtCore import QObject, pyqtSlot

from .message_box_mixin import MessageBoxMixin
from ..utils import ColumnRole


class LayerColumnsDialog(QtWidgets.QDialog, MessageBoxMixin):
    """Диалоговое окно для сопоставления полей таблиц и их атрибутов"""

    def __init__(
            self,
            model: ColumnsConfigModel,
            controller: InitDialogsController,
            parent: QObject = None
    ):
        super().__init__(parent)

        self.__model = model
        self.__controller = controller
        self.__step_finished = False

        self.setupUi()

    def __connect(self):
        self.__model.available_columns_changed.connect(self.__update_columns_table)
        self.__model.mappings_changed.connect(self.__update_columns_table)

        self.__controller.column_config_failed.connect(self.__on_column_config_failed)
        self.__controller.columns_configured.connect(self.__accept_step)

        self.buttonBox.accepted.connect(self.__on_accept)
        self.buttonBox.rejected.connect(self.close)

    def setupUi(self):
        self.setObjectName("TableColumnsDialog")
        self.resize(900, 700)

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
        QtCore.QMetaObject.connectSlotsByName(self)
        self.__connect()

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("TableColumnsDialog", "Шаг 3: сопоставление полей выбранных таблиц"))
        self.label.setText(_translate("TableColumnsDialog", "Укажите назначение каждого из столбцов для таблиц."))

    def showEvent(self, event, **kwargs):
        super().showEvent(event)
        self.__update_columns_table()

    def closeEvent(self, event, **kwargs):
        if self.__step_finished:
            event.accept()
            return

        close_question = self._show_question(
            "Для продолжения требуется выполнить настройку полей.\nВы уверены, что хотите закрыть мастер подключения?"
        )
        if close_question:
            self.__controller.initialization_cancelled()
            event.accept()
        else:
            event.ignore()

    def __on_accept(self):
        self.__controller.column_setup_step_finish()

    @pyqtSlot(str)
    def __on_column_config_failed(self, message: str):
        self._show_error(message)

    def __accept_step(self):
        self.__step_finished = True
        self.accept()

    @pyqtSlot(dict)
    def __update_columns_table(self, _=None):
        layers = self.__model.layers
        mappings = self.__model.mappings

        self.tableWidget.blockSignals(True)
        self.tableWidget.setRowCount(len(ColumnRole))
        self.tableWidget.setColumnCount(len(layers))

        for col_index, layer in enumerate(layers):
            self.tableWidget.setHorizontalHeaderItem(
                col_index,
                QtWidgets.QTableWidgetItem(layer.name)
            )

        for row_index, role in enumerate(ColumnRole):
            self.tableWidget.setVerticalHeaderItem(
                row_index,
                QtWidgets.QTableWidgetItem(role.value)
            )

            for col_index, layer in enumerate(layers):
                self.tableWidget.setCellWidget(
                    row_index,
                    col_index,
                    self.__create_cell_combobox(layer.name, role, mappings.get(layer.name, {}).get(role))
                )

        self.tableWidget.blockSignals(False)

    def __create_cell_combobox(self, layer_name: str, role: ColumnRole, selected_column: str | None):
        combo = QtWidgets.QComboBox()
        combo.setObjectName("colTypeComboBox")
        combo.addItem("-- Не задано --", None)

        for column in self.__model.available_columns.get(layer_name, []):
            label = self.__column_label(column)
            combo.addItem(label, column.name)

            if selected_column and column.name == selected_column:
                combo.setCurrentIndex(combo.count() - 1)

        combo.currentIndexChanged.connect(
            lambda _, c=combo, table=layer_name, column_role=role:
                self.__controller.change_column_info(table, c.currentData(), column_role)
        )
        return combo

    def __column_label(self, column: ColumnInfo) -> str:
        if column.data_type:
            return f"{column.name} ({column.data_type})"
        return column.name
