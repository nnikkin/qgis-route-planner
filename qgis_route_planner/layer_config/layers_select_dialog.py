# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .layer_dialogs_controller import LayerDialogsController
    from .layer_config_model import LayerConfigModel, Layer

from qgis.PyQt import QtCore, QtWidgets
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QObject, pyqtSlot

from qgis_route_planner.presentation.message_box_mixin import MessageBoxMixin
from .layer_role import LayerRole


class LayersSelectDialog(QtWidgets.QDialog, MessageBoxMixin):
    """ Диалоговое окно выбора слоя для обработки """

    def __init__(
            self,
            model: LayerConfigModel,
            controller: LayerDialogsController,
            parent: QObject = None
    ):
        super().__init__(parent)

        self.__model: LayerConfigModel = model
        self.__controller: LayerDialogsController = controller

        self.__available_layers: list = []
        self.__step_finished = False

        self.__setupUi()

    def __connect(self):
        self.pushItemToTableButton.clicked.connect(self.__on_push_to_table_clicked)
        self.pushItemToListButton.clicked.connect(self.__on_push_to_list_clicked)
        self.buttonBox.accepted.connect(self.__on_accept)
        self.buttonBox.rejected.connect(self.close)
        self.backButton.clicked.connect(self.__on_back)

        self.__model.layers_changed.connect(self.__update_layers_table)

        self.__controller.layers_selected.connect(self.__accept_step)
        self.__controller.layer_selection_failed.connect(self.__on_layer_selection_failed)

    def __setupUi(self):
        self.setObjectName("SelectLayersDialog")
        self.resize(800, 400)
        self.setWindowIcon(QIcon(":/plugins/qgis_route_planner/plugin_icon"))

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")

        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")

        self.label = QtWidgets.QLabel(self)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.listWidget = QtWidgets.QListWidget(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listWidget.sizePolicy().hasHeightForWidth())

        self.listWidget.setSizePolicy(sizePolicy)
        self.listWidget.setObjectName("listWidget")

        self.horizontalLayout.addWidget(self.listWidget)

        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetMinimumSize)
        self.verticalLayout_2.setContentsMargins(-1, -1, 0, -1)
        self.verticalLayout_2.setObjectName("verticalLayout_2")

        self.pushItemToTableButton = QtWidgets.QPushButton(self)
        self.pushItemToTableButton.setObjectName("pushItemToTableButton")
        self.verticalLayout_2.addWidget(self.pushItemToTableButton)

        self.pushItemToListButton = QtWidgets.QPushButton(self)
        self.pushItemToListButton.setObjectName("pushItemToListButton")
        self.verticalLayout_2.addWidget(self.pushItemToListButton)

        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.tableWidget = QtWidgets.QTableWidget(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableWidget.sizePolicy().hasHeightForWidth())

        self.tableWidget.setSizePolicy(sizePolicy)
        self.tableWidget.setSizeIncrement(QtCore.QSize(0, 0))
        self.tableWidget.setProperty("showDropIndicator", False)
        self.tableWidget.setDragDropOverwriteMode(False)
        self.tableWidget.setAlternatingRowColors(False)
        self.tableWidget.setCornerButtonEnabled(True)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        self.tableWidget.horizontalHeader().setSortIndicatorShown(False)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.verticalHeader().setSortIndicatorShown(False)
        self.tableWidget.verticalHeader().setStretchLastSection(False)
        self.tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.horizontalLayout.addWidget(self.tableWidget)

        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)

        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.buttonBox.sizePolicy().hasHeightForWidth())

        self.buttonBox.setSizePolicy(sizePolicy)
        self.buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel |
                                          QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setCenterButtons(False)
        self.buttonBox.setObjectName("buttonBox")
        self.backButton = self.buttonBox.addButton(
            "Назад",
            QtWidgets.QDialogButtonBox.ButtonRole.ActionRole
        )
        self.backButton.setObjectName("backButton")
        self.verticalLayout.addWidget(self.buttonBox)

        self.setTabOrder(self.listWidget, self.pushItemToTableButton)
        self.setTabOrder(self.pushItemToTableButton, self.pushItemToListButton)
        self.setTabOrder(self.pushItemToListButton, self.tableWidget)

        self.__retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)
        self.__connect()

    def __retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("Dialog", "Шаг 2: выбор слоёв"))
        self.label.setText(_translate("Dialog", "Выберите слои из базы данных для обработки."))
        self.pushItemToTableButton.setText(_translate("Dialog", ">>"))
        self.pushItemToListButton.setText(_translate("Dialog", "<<"))
        self.backButton.setText(_translate("Dialog", "Назад"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("Dialog", "Название"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("Dialog", "Назначение слоя"))

    def showEvent(self, event, **kwargs):
        super().showEvent(event)
        self.__step_finished = False
        self.__available_layers = []
        self.listWidget.clear()
        self.__fill_list()
        self.__update_layers_table(self.__model.selected_layers)

    def closeEvent(self, event, **kwargs):
        if self.__step_finished:
            event.accept()
            return

        close_question = self._show_question(self,
            "Для продолжения требуется выбрать слои.\nВы уверены, что хотите закрыть мастер подключения?",
            "Внимание"
        )
        if close_question:
            self.__controller.cancel_initialization()
            event.accept()
        else:
            event.ignore()

    def __on_push_to_table_clicked(self):
        selected_item = self.listWidget.currentItem()
        if not selected_item:
            self._show_warning(self, "Выберите название слоя из списка слева.")
            return
        l_name = selected_item.text()
        self.__controller.add_layer_to_config(layer_name=l_name, layer_role=LayerRole.ROADS)

    def __on_push_to_list_clicked(self):
        selected_rows = self.tableWidget.selectionModel().selectedRows()

        if not selected_rows:
            self._show_warning(self, "Выберите строку в таблице справа.")
            return

        self.__controller.remove_layer_from_config(selected_rows[0].row())

    def __on_accept(self):
        self.__controller.layer_select_step_finish()

    def __on_back(self):
        self.__step_finished = True
        self.reject()
        self.__controller.layer_select_step_back()

    def __accept_step(self):
        self.__step_finished = True
        self.accept()

    @pyqtSlot(str)
    def __on_layer_selection_failed(self, message: str):
        self._show_warning(self, message)

    def __on_combobox_role_changed(self, row, text):
        role = LayerRole.from_value(text)
        self.__controller.change_layer_role(row, role)

    @pyqtSlot(list)
    def __update_layers_table(self, layers: list):
        self.tableWidget.blockSignals(True)
        self.tableWidget.setRowCount(0)

        for row, layer in enumerate(layers):
            self.__create_table_row(layer)

        self.listWidget.clear()
        chosen_names = {l.name for l in layers}
        for name in self.__available_layers:
            if name not in chosen_names:
                self.listWidget.addItem(name)

        self.tableWidget.blockSignals(False)

    def __create_role_combobox(self, role: LayerRole = LayerRole.ROADS):
        roleComboBox = QtWidgets.QComboBox()
        roleComboBox.setObjectName("roleComboBox")
        for index, e in enumerate(LayerRole):
            roleComboBox.addItem(e.value)
            if e == role:
                roleComboBox.setCurrentIndex(index)
        return roleComboBox

    def __create_table_row(self, layer: Layer):
        row_count = self.tableWidget.rowCount()

        role_cbox = self.__create_role_combobox(layer.role)
        role_cbox.currentTextChanged.connect(
            lambda text, r=row_count: self.__on_combobox_role_changed(r, text)
        )

        self.tableWidget.insertRow(row_count)
        self.tableWidget.setItem(row_count, 0, QtWidgets.QTableWidgetItem(layer.name))
        self.tableWidget.setCellWidget(row_count, 1, role_cbox)

    def __fill_list(self):
        layers = self.__controller.get_layers()
        self.__available_layers = layers
        self.listWidget.addItems(self.__available_layers)
