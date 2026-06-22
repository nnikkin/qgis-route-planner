# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .layer_dialogs_controller import LayerDialogsController
    from .cols_config_model import ColumnsConfigModel
    from .cols_config_model import ColumnInfo

from qgis.PyQt import QtCore, QtWidgets
from qgis.PyQt.QtGui import QBrush, QColor, QIcon
from qgis.PyQt.QtCore import QObject, pyqtSlot

from qgis_route_planner.presentation import MessageBoxMixin
from .column_role import ColumnRole
from .layer_role import LayerRole


class LayerColumnsDialog(QtWidgets.QDialog, MessageBoxMixin):
    """ Диалоговое окно для сопоставления полей таблиц и их атрибутов """

    def __init__(
            self,
            model: ColumnsConfigModel,
            controller: LayerDialogsController,
            parent: QObject = None
    ):
        super().__init__(parent)

        self.__model = model
        self.__controller = controller
        self.__step_finished = False

        self.__setupUi()

    def __connect(self):
        self.__model.available_columns_changed.connect(self.__update_columns_table)
        self.__model.mappings_changed.connect(self.__update_columns_table)

        self.__controller.column_config_failed.connect(self.__on_column_config_failed)
        self.__controller.columns_configured.connect(self.__accept_step)

        self.buttonBox.accepted.connect(self.__on_accept)
        self.buttonBox.rejected.connect(self.close)
        self.backButton.clicked.connect(self.__on_back)

    def __setupUi(self):
        self.setObjectName("TableColumnsDialog")
        self.resize(900, 700)
        self.setWindowIcon(QIcon(":/plugins/qgis_route_planner/plugin_icon"))

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
        self.backButton = self.buttonBox.addButton(
            "Назад",
            QtWidgets.QDialogButtonBox.ButtonRole.ActionRole
        )
        self.backButton.setObjectName("backButton")
        self.verticalLayout.addWidget(self.buttonBox)

        self.__retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)
        self.__connect()

    def __retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("TableColumnsDialog", "Шаг 3: сопоставление полей выбранных таблиц"))
        self.label.setText(_translate("TableColumnsDialog", "Укажите назначение каждого из столбцов для таблиц."))
        self.backButton.setText(_translate("TableColumnsDialog", "Назад"))

    def showEvent(self, event, **kwargs):
        super().showEvent(event)
        self.__step_finished = False
        self.__update_columns_table()

    def closeEvent(self, event, **kwargs):
        if self.__step_finished:
            event.accept()
            return

        close_question = self._show_question(
            "Для продолжения требуется выполнить настройку полей.\nВы уверены, что хотите закрыть мастер подключения?"
        )
        if close_question:
            self.__controller.cancel_initialization()
            event.accept()
        else:
            event.ignore()

    def __on_accept(self):
        self.__controller.column_setup_step_finish()

    def __on_back(self):
        self.__step_finished = True
        self.reject()
        self.__controller.column_setup_step_back()

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
            required_labels = [
                role.value
                for role in self.__model.required_roles_for_layer(layer.role)
            ]
            header_text = f"{layer.name}\n{layer.role.value}"
            if required_labels:
                header_text += "\n* обязательные поля"

            header_item = QtWidgets.QTableWidgetItem(header_text)
            header_item.setToolTip(
                "Обязательные поля:\n" + "\n".join(required_labels)
                if required_labels else "Для этого слоя обязательных полей нет."
            )
            self.tableWidget.setHorizontalHeaderItem(
                col_index,
                header_item
            )

        for row_index, role in enumerate(ColumnRole):
            self.tableWidget.setVerticalHeaderItem(
                row_index,
                QtWidgets.QTableWidgetItem(role.value)
            )

            for col_index, layer in enumerate(layers):
                item = self.__create_status_item(layer.role, role)
                self.tableWidget.setItem(row_index, col_index, item)
                self.tableWidget.setCellWidget(
                    row_index,
                    col_index,
                    self.__create_cell_combobox(layer, role, mappings.get(layer.name, {}).get(role))
                )

        self.tableWidget.blockSignals(False)

    def __create_cell_combobox(self, layer, role: ColumnRole, selected_column: str | None):
        combo = QtWidgets.QComboBox()
        combo.setObjectName("colTypeComboBox")
        is_applicable = self.__model.is_role_applicable(layer.role, role)
        is_required = self.__model.is_role_required(layer.role, role)

        if not is_applicable:
            combo.addItem("Не используется для этого типа слоя", None)
            combo.setEnabled(False)
            combo.setToolTip("Это поле не применяется для роли слоя.")
            return combo

        combo.addItem("-- Обязательное поле --" if is_required else "-- Не задано --", None)
        combo.setToolTip(
            "Обязательное поле для этой роли слоя."
            if is_required else "Необязательное поле для этой роли слоя."
        )

        for column in self.__model.available_columns.get(layer.name, []):
            label = self.__column_label(column)
            combo.addItem(label, column.name)

            if selected_column and column.name == selected_column:
                combo.setCurrentIndex(combo.count() - 1)

        combo.currentIndexChanged.connect(
            lambda _, c=combo, table=layer.name, column_role=role:
                self.__controller.change_column_info(table, c.currentData(), column_role)
        )

        if is_required and not selected_column:
            combo.setStyleSheet("QComboBox { background-color: #fff3cd; }")
        return combo

    def __column_label(self, column: ColumnInfo) -> str:
        if column.data_type:
            return f"{column.name} ({column.data_type})"
        return column.name

    def __create_status_item(self, layer_role: LayerRole, column_role: ColumnRole):
        item = QtWidgets.QTableWidgetItem()
        item.setFlags(QtCore.Qt.ItemFlag.NoItemFlags)

        if not self.__model.is_role_applicable(layer_role, column_role):
            item.setBackground(QBrush(QColor("#eeeeee")))
            item.setToolTip("Не используется для этой роли слоя.")
        elif self.__model.is_role_required(layer_role, column_role):
            item.setBackground(QBrush(QColor("#fff3cd")))
            item.setToolTip("Обязательное поле.")
        else:
            item.setToolTip("Необязательное поле.")

        return item
