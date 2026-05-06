# -*- coding: utf-8 -*-
from qgis.PyQt import QtCore, QtWidgets
from qgis.PyQt.QtCore import QModelIndex
from qgis.PyQt.QtWidgets import QMessageBox

from qgis_route_planner.models.geometry_types import GeometryType
from qgis_route_planner.views.base_qdialog import BaseQDialog


class SelectLayersDialog(BaseQDialog):
    """Диалоговое окно выбора слоя для обработки"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi()

    def setupUi(self):
        self.setObjectName("SelectLayersDialog")
        self.resize(700, 400)

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

        self.addItemToTableButton = QtWidgets.QPushButton(self)
        self.addItemToTableButton.setObjectName("addItemToTableButton")
        self.addItemToTableButton.clicked.connect(self.__move_selected_to_table)
        self.verticalLayout_2.addWidget(self.addItemToTableButton)

        self.pushItemToListButton = QtWidgets.QPushButton(self)
        self.pushItemToListButton.setObjectName("pushItemToListButton")
        self.pushItemToListButton.clicked.connect(self.__move_selected_to_list)
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
        self.tableWidget.setColumnCount(2)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
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
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)
        self.setTabOrder(self.listWidget, self.addItemToTableButton)
        self.setTabOrder(self.addItemToTableButton, self.pushItemToListButton)
        self.setTabOrder(self.pushItemToListButton, self.tableWidget)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("Dialog", "Шаг 2: выбор таблицы"))
        self.label.setText(_translate("Dialog", "Выберите слои с геометрией LineString из базы данных для обработки."))
        self.addItemToTableButton.setText(_translate("Dialog", ">>"))
        self.pushItemToListButton.setText(_translate("Dialog", "<<"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("Dialog", "Название таблицы"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("Dialog", "Тип геометрии"))

    @property
    def initialization_completed(self) -> bool:
        return self.__initialization_completed

    @initialization_completed.setter
    def initialization_completed(self, value: bool):
        self.__initialization_completed = value

    def closeEvent(self, event):
        close_question = QMessageBox.question(
            self,
            "Внимание",
            "Для продолжения требуется выбрать таблицу.\nВы уверены, что хотите закрыть мастер подключения?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if close_question == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def __create_geometry_combobox(self):
        geometryComboBox = QtWidgets.QComboBox()
        geometryComboBox.setObjectName("geometryComboBox")
        for e in GeometryType:
            geometryComboBox.addItem(e.value)
        return geometryComboBox

    def fill_list(self, table_names: list[str]):
        self.listWidget.addItems(table_names)

    def get_table_rows(self) -> list[tuple[str, GeometryType]]:
        result = []

        for row in range(self.tableWidget.rowCount()):
            table_name_item = self.tableWidget.item(row, 0)
            geometry_combo = self.tableWidget.cellWidget(row, 1)

            if table_name_item is None or geometry_combo is None:
                continue

            table_name = table_name_item.text()
            geometry_label = geometry_combo.currentText()
            geometry_type = GeometryType.from_value(geometry_label)

            result.append((table_name, geometry_type))

        return result

    def __get_list_selection(self) -> QModelIndex:
        return self.listWidget.selectionModel().selectedRows()[0]

    def __get_table_selection(self) -> QModelIndex:
        return self.tableWidget.selectionModel().selectedRows()[0]

    def __add_selected_to_list(self, item_name: str):
        self.listWidget.addItem(item_name)

    def __remove_selected_from_list(self):
        selection = self.__get_list_selection()
        item_str = selection.data()
        self.listWidget.takeItem(selection.row())
        return item_str

    def __add_selected_to_table(self, item_name: str):
        row_count = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row_count)
        self.tableWidget.setItem(row_count, 0, QtWidgets.QTableWidgetItem(item_name))
        self.tableWidget.setCellWidget(row_count, 1, self.__create_geometry_combobox())

    def __remove_selected_from_table(self):
        selection = self.__get_table_selection()
        item_str = selection.data()
        self.tableWidget.removeRow(selection.row())
        return item_str

    def __move_selected_to_table(self):
        try:
            tmp = self.__remove_selected_from_list()
            self.__add_selected_to_table(tmp)
        except IndexError:
            QtWidgets.QMessageBox.warning(self, "Ошибка",
                                          f"Выберите значение из списка слева.", QtWidgets.QMessageBox.Ok)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Ошибка __listToTable", f"{type(e)}\n{e}", QtWidgets.QMessageBox.Ok)

    def __move_selected_to_list(self):
        try:
            tmp = self.__remove_selected_from_table()
            self.__add_selected_to_list(tmp)
        except IndexError:
            QtWidgets.QMessageBox.warning(self, "Ошибка",
                                          f"В таблице отсутствуют записи.\nСначала перенесите таблицу из списка слева.",
                                          QtWidgets.QMessageBox.Ok)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Ошибка __tableToList", f"{type(e)}\n{e}", QtWidgets.QMessageBox.Ok)