# -*- coding: utf-8 -*-
from __future__ import annotations

from qgis.PyQt import QtCore, QtWidgets
from qgis.PyQt.QtCore import QObject, pyqtSlot

from ..views import MessageBoxMixin
from ..controllers import RestrictionDialogController
from ..data.restrictions import RestrictionType


class RestrictionDialog(QtWidgets.QDialog, MessageBoxMixin):
    """Диалог организации ограничений"""

    def __init__(
            self,
            controller: RestrictionDialogController,
            parent: QObject = None
    ):
        super().__init__(parent)

        self.__controller = controller

        self.setupUi()
        self.__connect()

    def setupUi(self):
        self.setObjectName("RestrictionDialog")
        self.resize(832, 600)

        # Главный layout
        self.DialogLayout = QtWidgets.QHBoxLayout(self)
        self.DialogLayout.setObjectName("DialogLayout")

        # Левая часть окна
        self.leftLayout = QtWidgets.QVBoxLayout()
        self.leftLayout.setObjectName("leftLayout")

        self.restrictionListWidget = QtWidgets.QListWidget(self)
        self.restrictionListWidget.setObjectName("restrictionListWidget")
        self.leftLayout.addWidget(self.restrictionListWidget)

        self.btnLayout = QtWidgets.QGridLayout()
        self.btnLayout.setObjectName("btnLayout")
        self.createRestrictionButton = QtWidgets.QPushButton("Новое ограничение", self)
        self.createRestrictionButton.setObjectName("createRestrictionButton")
        self.editRestrictionButton = QtWidgets.QPushButton("Изменить", self)
        self.editRestrictionButton.setObjectName("editRestrictionButton")
        self.editRestrictionButton.setEnabled(False)
        self.deleteRestrictionButton = QtWidgets.QPushButton("Удалить", self)
        self.deleteRestrictionButton.setObjectName("deleteRestrictionButton")
        self.deleteRestrictionButton.setEnabled(False)

        self.btnLayout.addWidget(self.createRestrictionButton, 0, 0)
        self.btnLayout.addWidget(self.editRestrictionButton, 1, 0)
        self.btnLayout.addWidget(self.deleteRestrictionButton, 2, 0)
        self.leftLayout.addLayout(self.btnLayout)
        self.DialogLayout.addLayout(self.leftLayout)

        # Правая часть окна
        self.restrictionForm = QtWidgets.QGroupBox("Настройки ограничения", self)
        self.restrictionForm.setObjectName("restrictionForm")

        self.restrictionFormLayout = QtWidgets.QVBoxLayout(self.restrictionForm)
        self.restrictionFormLayout.setObjectName("restrictionFormLayout")

        # Форма с общими полями
        self.generalFormLayout = QtWidgets.QFormLayout()
        self.generalFormLayout.setObjectName("generalFormLayout")

        self.label_type = QtWidgets.QLabel("Тип:", self.restrictionForm)
        self.restrictionTypeComboBox = QtWidgets.QComboBox(self.restrictionForm)
        for rt in RestrictionType:
            self.restrictionTypeComboBox.addItem(rt.value, rt)
        self.restrictionTypeComboBox.setEnabled(False)
        self.generalFormLayout.addRow(self.label_type, self.restrictionTypeComboBox)

        self.label_name = QtWidgets.QLabel("Название:", self.restrictionForm)
        self.restrictionNameEdit = QtWidgets.QLineEdit(self.restrictionForm)
        self.restrictionNameEdit.setEnabled(False)
        self.generalFormLayout.addRow(self.label_name, self.restrictionNameEdit)

        self.label_comment = QtWidgets.QLabel("Комментарий:", self.restrictionForm)
        self.restrictionCommentEdit = QtWidgets.QLineEdit(self.restrictionForm)
        self.restrictionCommentEdit.setEnabled(False)
        self.generalFormLayout.addRow(self.label_comment, self.restrictionCommentEdit)

        self.restrictionFormLayout.addLayout(self.generalFormLayout)

        # Стек для разных типов ограничений
        self.stackedWidget = QtWidgets.QStackedWidget(self.restrictionForm)
        self.stackedWidget.setObjectName("stackedWidget")

        # Страница SIMPLE
        self.pageSimple = self.__build_simple_page()
        self.stackedWidget.addWidget(self.pageSimple)

        # Страница DIMENSION
        self.pageDimension = self.__build_dimension_page()
        self.stackedWidget.addWidget(self.pageDimension)

        # Страница TEMPORARY
        self.pageTemporary = self.__build_temporary_page()
        self.stackedWidget.addWidget(self.pageTemporary)

        self.restrictionFormLayout.addWidget(self.stackedWidget)

        # Кнопки диалога
        self.dialogButtonsLayout = QtWidgets.QHBoxLayout()
        self.saveRestrictionButton = QtWidgets.QPushButton("Сохранить", self.restrictionForm)
        self.saveRestrictionButton.setEnabled(False)
        self.cancelRestrictionEditButton = QtWidgets.QPushButton("Отмена", self.restrictionForm)
        self.cancelRestrictionEditButton.setEnabled(False)

        self.dialogButtonsLayout.addWidget(self.saveRestrictionButton)
        self.dialogButtonsLayout.addWidget(self.cancelRestrictionEditButton)
        self.restrictionFormLayout.addLayout(self.dialogButtonsLayout)

        self.DialogLayout.addWidget(self.restrictionForm)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

    def __build_simple_page(self) -> QtWidgets.QtWidgets.QtWidget:
        page = QtWidgets.QtWidgets.QtWidget()
        layout = QtWidgets.QVBoxLayout(page)

        self.simpleNodesList = QtWidgets.QListWidget()
        self.simpleNodesList.setMaximumHeight(100)
        self.simpleNodesList.setEnabled(False)

        btn_layout = QtWidgets.QHBoxLayout()
        self.simpleSelectPointBtn = QtWidgets.QPushButton("Выбрать точку на карте")
        self.simpleSelectPointBtn.setEnabled(False)
        self.simpleRemovePointBtn = QtWidgets.QPushButton("Убрать выбранную")
        self.simpleRemovePointBtn.setEnabled(False)
        btn_layout.addWidget(self.simpleSelectPointBtn)
        btn_layout.addWidget(self.simpleRemovePointBtn)

        layout.addWidget(QtWidgets.QLabel("Точки ограничения:"))
        layout.addWidget(self.simpleNodesList)
        layout.addLayout(btn_layout)

        return page

    def __build_dimension_page(self) ->QtWidgets. QtWidgets.QtWidget:
        page = QtWidgets.QtWidgets.QtWidget()
        layout = QtWidgets.QVBoxLayout(page)

        form_layout = QtWidgets.QFormLayout()

        self.dimHeightSpin = QtWidgets.QDoubleSpinBox()
        self.dimHeightSpin.setSuffix(" м")
        self.dimHeightSpin.setMaximum(99.0)
        self.dimHeightSpin.setEnabled(False)

        self.dimWidthSpin = QtWidgets.QDoubleSpinBox()
        self.dimWidthSpin.setSuffix(" м")
        self.dimWidthSpin.setMaximum(99.0)
        self.dimWidthSpin.setEnabled(False)

        self.dimLengthSpin = QtWidgets.QDoubleSpinBox()
        self.dimLengthSpin.setSuffix(" м")
        self.dimLengthSpin.setMaximum(99.0)
        self.dimLengthSpin.setEnabled(False)

        self.dimWeightSpin = QtWidgets.QDoubleSpinBox()
        self.dimWeightSpin.setSuffix(" т")
        self.dimWeightSpin.setMaximum(999.0)
        self.dimWeightSpin.setEnabled(False)

        form_layout.addRow("Макс. высота:", self.dimHeightSpin)
        form_layout.addRow("Макс. ширина:", self.dimWidthSpin)
        form_layout.addRow("Макс. длина:", self.dimLengthSpin)
        form_layout.addRow("Макс. вес:", self.dimWeightSpin)

        self.dimNodesList = QtWidgets.QListWidget()
        self.dimNodesList.setMaximumHeight(100)
        self.dimNodesList.setEnabled(False)

        btn_layout = QtWidgets.QHBoxLayout()
        self.dimSelectPointBtn = QtWidgets.QPushButton("Выбрать точку на карте")
        self.dimSelectPointBtn.setEnabled(False)
        self.dimRemovePointBtn = QtWidgets.QPushButton("Убрать выбранную")
        self.dimRemovePointBtn.setEnabled(False)
        btn_layout.addWidget(self.dimSelectPointBtn)
        btn_layout.addWidget(self.dimRemovePointBtn)

        layout.addLayout(form_layout)
        layout.addWidget(QtWidgets.QLabel("Точки ограничения:"))
        layout.addWidget(self.dimNodesList)
        layout.addLayout(btn_layout)

        return page

    def __build_temporary_page(self) -> QtWidgets.QtWidget:
        page = QtWidgets.QtWidget()
        layout = QtWidgets.QVBoxLayout(page)

        form_layout = QtWidgets.QFormLayout()

        self.tmpDateFrom = QtWidgets.QDateTimeEdit()
        self.tmpDateFrom.setCalendarPopup(True)
        self.tmpDateFrom.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.tmpDateFrom.setEnabled(False)

        self.tmpDateTo = QtWidgets.QDateTimeEdit()
        self.tmpDateTo.setCalendarPopup(True)
        self.tmpDateTo.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.tmpDateTo.setEnabled(False)

        form_layout.addRow("Начало действия:", self.tmpDateFrom)
        form_layout.addRow("Конец действия:", self.tmpDateTo)

        self.tmpNodesList = QtWidgets.QListWidget()
        self.tmpNodesList.setMaximumHeight(100)
        self.tmpNodesList.setEnabled(False)

        btn_layout = QtWidgets.QHBoxLayout()
        self.tmpSelectPointBtn = QtWidgets.QPushButton("Выбрать точку на карте")
        self.tmpSelectPointBtn.setEnabled(False)
        self.tmpRemovePointBtn = QtWidgets.QPushButton("Убрать выбранную")
        self.tmpRemovePointBtn.setEnabled(False)
        btn_layout.addWidget(self.tmpSelectPointBtn)
        btn_layout.addWidget(self.tmpRemovePointBtn)

        layout.addLayout(form_layout)
        layout.addWidget(QtWidgets.QLabel("Точки ограничения:"))
        layout.addWidget(self.tmpNodesList)
        layout.addLayout(btn_layout)

        return page

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("RestrictionDialog", "Настройки ограничений"))
        self.createRestrictionButton.setText(_translate("RestrictionDialog", "Новое ограничение"))
        self.deleteRestrictionButton.setText(_translate("RestrictionDialog", "Удалить"))
        self.editRestrictionButton.setText(_translate("RestrictionDialog", "Изменить"))
        self.saveRestrictionButton.setText(_translate("RestrictionDialog", "Сохранить"))
        self.cancelRestrictionEditButton.setText(_translate("RestrictionDialog", "Отмена"))

    def __connect(self):
        self.restrictionTypeComboBox.currentIndexChanged.connect(self.__on_type_changed)
        self.restrictionListWidget.itemSelectionChanged.connect(
            self.__controller.on_restriction_selected
        )
        self.createRestrictionButton.clicked.connect(self.__controller.on_create_restriction)
        self.editRestrictionButton.clicked.connect(self.__controller.on_edit_restriction)
        self.deleteRestrictionButton.clicked.connect(self.__controller.on_delete_restriction)
        self.saveRestrictionButton.clicked.connect(self.__controller.on_save_restriction)
        self.cancelRestrictionEditButton.clicked.connect(self.__controller.on_cancel_edit)

        # Кнопки выбора точки на карте
        self.simpleSelectPointBtn.clicked.connect(self.__on_select_point_clicked)
        self.dimSelectPointBtn.clicked.connect(self.__on_select_point_clicked)
        self.tmpSelectPointBtn.clicked.connect(self.__on_select_point_clicked)

        # Кнопки удаления точки
        self.simpleRemovePointBtn.clicked.connect(
            lambda: self.__remove_selected_point(self.simpleNodesList)
        )
        self.dimRemovePointBtn.clicked.connect(
            lambda: self.__remove_selected_point(self.dimNodesList)
        )
        self.tmpRemovePointBtn.clicked.connect(
            lambda: self.__remove_selected_point(self.tmpNodesList)
        )

        self.__controller.show_error.connect(self.__show_error)
        self.__controller.show_warning.connect(self.__show_warning)
        self.__controller.show_info.connect(self.__show_info)

    def __on_select_point_clicked(self):
        """Обработчик нажатия на кнопку выбора точки"""
        dialog = self.__show_with_point_selection()

        if dialog.Ok:
            self.hide()
            self.__controller.on_select_point_on_map()

    @pyqtSlot(int)
    def __on_type_changed(self, index: int):
        rt = self.restrictionTypeComboBox.itemData(index)
        if rt == RestrictionType.SIMPLE:
            self.stackedWidget.setCurrentIndex(0)
        elif rt == RestrictionType.DIMENSION:
            self.stackedWidget.setCurrentIndex(1)
        elif rt == RestrictionType.TEMPORARY:
            self.stackedWidget.setCurrentIndex(2)

    def __remove_selected_point(self, list_widget: QtWidgets.QListWidget):
        row = list_widget.currentRow()
        if row >= 0:
            list_widget.takeItem(row)

    def get_current_type(self) -> RestrictionType:
        return self.restrictionTypeComboBox.currentData()

    def get_current_nodes_list(self) -> QtWidgets.QListWidget:
        """Возвращает список точек активной страницы"""
        idx = self.stackedWidget.currentIndex()
        return [self.simpleNodesList, self.dimNodesList, self.tmpNodesList][idx]

    def get_name(self) -> str:
        return self.restrictionNameEdit.text().strip()

    def get_comment(self) -> str:
        return self.restrictionCommentEdit.text().strip()

    def get_dimension_values(self) -> tuple[float, float, float, float]:
        return (
            self.dimHeightSpin.value(),
            self.dimWidthSpin.value(),
            self.dimLengthSpin.value(),
            self.dimWeightSpin.value()
        )

    def get_temporary_dates(self):
        return (
            self.tmpDateFrom.dateTime(),
            self.tmpDateTo.dateTime()
        )

    def add_node_to_list(self, node_id: int, x: float, y: float):
        """Добавить точку в список активной страницы"""
        nodes_list = self.get_current_nodes_list()
        item = QtWidgets.QListWidgetItem(f"Node {node_id} ({x:.5f}, {y:.5f})")
        item.setData(QtCore.Qt.ItemDataRole.UserRole, node_id)
        nodes_list.addItem(item)

    def get_node_ids(self) -> list[int]:
        """Получить все node_id из активной страницы"""
        nodes_list = self.get_current_nodes_list()
        return [
            nodes_list.item(i).data(QtCore.Qt.ItemDataRole.UserRole)
            for i in range(nodes_list.count())
        ]

    def set_form_enabled(self, enabled: bool):
        """Включить/выключить форму редактирования"""
        self.restrictionTypeComboBox.setEnabled(enabled)
        self.restrictionNameEdit.setEnabled(enabled)
        self.restrictionCommentEdit.setEnabled(enabled)
        self.saveRestrictionButton.setEnabled(enabled)
        self.cancelRestrictionEditButton.setEnabled(enabled)

        idx = self.stackedWidget.currentIndex()
        if idx == 0:  # SIMPLE
            self.simpleSelectPointBtn.setEnabled(enabled)
            self.simpleRemovePointBtn.setEnabled(enabled)
            self.simpleNodesList.setEnabled(enabled)
        elif idx == 1:  # DIMENSION
            self.dimHeightSpin.setEnabled(enabled)
            self.dimWidthSpin.setEnabled(enabled)
            self.dimLengthSpin.setEnabled(enabled)
            self.dimWeightSpin.setEnabled(enabled)
            self.dimSelectPointBtn.setEnabled(enabled)
            self.dimRemovePointBtn.setEnabled(enabled)
            self.dimNodesList.setEnabled(enabled)
        elif idx == 2:  # TEMPORARY
            self.tmpDateFrom.setEnabled(enabled)
            self.tmpDateTo.setEnabled(enabled)
            self.tmpSelectPointBtn.setEnabled(enabled)
            self.tmpRemovePointBtn.setEnabled(enabled)
            self.tmpNodesList.setEnabled(enabled)

    def set_list_buttons_enabled(self, enabled: bool):
        """Включить/выключить кнопки управления списком"""
        self.editRestrictionButton.setEnabled(enabled)
        self.deleteRestrictionButton.setEnabled(enabled)

    def clear_form(self):
        """Очистить форму"""
        self.restrictionNameEdit.clear()
        self.restrictionCommentEdit.clear()

        self.simpleNodesList.clear()

        self.dimNodesList.clear()
        self.dimHeightSpin.setValue(0)
        self.dimWidthSpin.setValue(0)
        self.dimLengthSpin.setValue(0)
        self.dimWeightSpin.setValue(0)

        self.tmpNodesList.clear()
        from qgis.PyQt.QtCore import QDateTime
        now = QDateTime.currentDateTime()
        self.tmpDateFrom.setDateTime(now)
        self.tmpDateTo.setDateTime(now.addDays(7))

    def load_restriction_to_form(self, restriction_data: dict):
        """Загрузить данные ограничения в форму"""
        self.restrictionNameEdit.setText(restriction_data.get("name", ""))
        self.restrictionCommentEdit.setText(restriction_data.get("comment", ""))

        # Установка типа
        type_id = restriction_data.get("restriction_type_id", 1)
        rt = {
            1: RestrictionType.SIMPLE,
            2: RestrictionType.DIMENSION,
            3: RestrictionType.TEMPORARY
        }.get(type_id, RestrictionType.SIMPLE)
        idx = self.restrictionTypeComboBox.findData(rt)
        if idx >= 0:
            self.restrictionTypeComboBox.setCurrentIndex(idx)

        # Загрузка node_id
        node_id = restriction_data.get("node_id")
        if node_id:
            self.add_node_to_list(node_id, 0, 0)

        # Загрузка специфичных данных
        value_text = restriction_data.get("value_text", "")
        if rt == RestrictionType.DIMENSION and value_text:
            pairs = dict(p.split("=", 1) for p in value_text.split(";") if "=" in p)
            self.dimHeightSpin.setValue(float(pairs.get("height", 0)))
            self.dimWidthSpin.setValue(float(pairs.get("width", 0)))
            self.dimLengthSpin.setValue(float(pairs.get("length", 0)))
            self.dimWeightSpin.setValue(float(pairs.get("weight", 0)))
        elif rt == RestrictionType.TEMPORARY and value_text:
            from qgis.PyQt.QtCore import QDateTime
            pairs = dict(p.split("=", 1) for p in value_text.split(";") if "=" in p)
            fmt = "yyyy-MM-dd HH:mm"
            if "from" in pairs:
                self.tmpDateFrom.setDateTime(QDateTime.fromString(pairs["from"], fmt))
            if "to" in pairs:
                self.tmpDateTo.setDateTime(QDateTime.fromString(pairs["to"], fmt))

    def __show_with_point_selection(self) -> 'QMessageBox':
        """Показать диалог с уведомлением о выборе точки"""
        return self._show_non_modal(
            "Выберите точку на карте для добавления в ограничение.\nПосле выбора точки диалог автоматически вернётся.",
            "Выбор точки"
        )