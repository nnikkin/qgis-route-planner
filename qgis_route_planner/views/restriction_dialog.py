# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..controllers import RestrictionDialogController
    from ..data.route import RestrictionModel

from qgis.PyQt import QtCore, QtWidgets
from qgis.PyQt.QtCore import pyqtSignal, QDateTime, QObject, QSize
from qgis.PyQt.QtGui import QIcon

from .message_box_mixin import MessageBoxMixin
from ..data.models import RestrictionType
from ..utils import FormMode


class RestrictionDialog(QtWidgets.QDialog, MessageBoxMixin):
    """Диалог организации ограничений"""

    def __init__(
            self,
            controller: RestrictionDialogController,
            model: RestrictionModel,
            parent: QObject = None
    ):
        super().__init__(parent)

        self.__controller = controller
        self.__model = model
        self.__current_point_type = "start"

        self.setupUi()
        self.__connect_controller_signals()
        self.__connect_ui_signals()

    def __connect_controller_signals(self):
        """Сигналы от контроллера к view"""
        self.__controller.show_error.connect(self.show_critical_message)
        self.__controller.show_warning.connect(self.show_warning_message)
        self.__controller.show_info.connect(self.show_info_message)
        self.__controller.open_requested.connect(self.open)
        self.__controller.point_selected.connect(self.on_point_selected_callback)
        self.__controller.load_restrictions_list.connect(self.set_restrictions_list)
        self.__controller.load_restriction_to_form.connect(self.load_restriction_to_form)
        self.__controller.set_form_state.connect(self.set_form_state)
        self.__controller.clear_form.connect(self.clear_form)
        self.__controller.set_list_buttons_enabled.connect(self.set_list_buttons_enabled)

    def __connect_ui_signals(self):
        """Сигналы от UI-элементов к контроллеру"""
        for rt in RestrictionType:
            self.restrictionTypeComboBox.addItem(rt.value, rt)
        self.restrictionTypeComboBox.currentIndexChanged.connect(self.__on_type_changed)

        self.restrictionListWidget.itemSelectionChanged.connect(
            self.__on_list_selection_changed
        )

        self.createRestrictionButton.clicked.connect(
            self.__controller.on_create_restriction
        )
        self.editRestrictionButton.clicked.connect(
            self.__controller.on_edit_restriction
        )
        self.deleteRestrictionButton.clicked.connect(
            self.__controller.on_delete_restriction
        )
        self.saveRestrictionButton.clicked.connect(self.__on_save_clicked)
        self.cancelRestrictionEditButton.clicked.connect(
            self.__controller.on_cancel_edit
        )

        self.radioButton_one.toggled.connect(self.__on_points_count_changed)
        self.radioButton_multiple.toggled.connect(self.__on_points_count_changed)

        self.chooseStartPointButton.clicked.connect(
            lambda: self.__on_select_point_clicked("start")
        )
        self.chooseMidPointsButton.clicked.connect(
            lambda: self.__on_select_point_clicked("mid")
        )
        self.chooseEndPointButton.clicked.connect(
            lambda: self.__on_select_point_clicked("end")
        )

        self.clearStartButton.clicked.connect(lambda: self.__clear_point("start"))
        self.clearMidListButton.clicked.connect(lambda: self.__clear_points("mid"))
        self.clearEndButton.clicked.connect(lambda: self.__clear_point("end"))

    def setupUi(self):
        self.setObjectName("RestrictionDialog")
        self.resize(832, 500)

        self.horizontalLayout = QtWidgets.QHBoxLayout(self)
        self.horizontalLayout.setObjectName("horizontalLayout")

        # Левая панель
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")

        self.restrictionListWidget = QtWidgets.QListWidget(self)
        self.restrictionListWidget.setObjectName("restrictionListWidget")
        sp = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding
        )
        self.restrictionListWidget.setSizePolicy(sp)
        self.verticalLayout.addWidget(self.restrictionListWidget)

        self.gridLayout_3 = QtWidgets.QGridLayout()
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.gridLayout_3.setContentsMargins(-1, -1, 0, 0)

        self.createRestrictionButton = QtWidgets.QPushButton(self)
        self.createRestrictionButton.setObjectName("createRestrictionButton")
        self.gridLayout_3.addWidget(self.createRestrictionButton, 0, 0, 1, 1)

        self.deleteRestrictionButton = QtWidgets.QPushButton(self)
        self.deleteRestrictionButton.setObjectName("deleteRestrictionButton")
        self.deleteRestrictionButton.setEnabled(False)
        self.gridLayout_3.addWidget(self.deleteRestrictionButton, 1, 0, 1, 1)

        self.editRestrictionButton = QtWidgets.QPushButton(self)
        self.editRestrictionButton.setObjectName("editRestrictionButton")
        self.editRestrictionButton.setEnabled(False)
        self.gridLayout_3.addWidget(self.editRestrictionButton, 2, 0, 1, 1)

        self.verticalLayout.addLayout(self.gridLayout_3)
        self.horizontalLayout.addLayout(self.verticalLayout)

        # Правая панель: форма
        self.restrictionForm = QtWidgets.QGroupBox(self)
        self.restrictionForm.setObjectName("restrictionForm")
        self.restrictionFormLayout = QtWidgets.QVBoxLayout(self.restrictionForm)
        self.restrictionFormLayout.setObjectName("restrictionFormLayout")
        self.restrictionFormLayout.setContentsMargins(-1, 9, -1, 0)

        self.typeFormLayout = QtWidgets.QFormLayout()
        self.typeFormLayout.setObjectName("typeFormLayout")

        self.label_2 = QtWidgets.QLabel(self.restrictionForm)
        self.label_2.setObjectName("label_2")
        self.typeFormLayout.setWidget(
            0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_2
        )

        self.restrictionTypeComboBox = QtWidgets.QComboBox(self.restrictionForm)
        self.restrictionTypeComboBox.setObjectName("restrictionTypeComboBox")
        self.restrictionTypeComboBox.setEnabled(False)
        self.typeFormLayout.setWidget(
            0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.restrictionTypeComboBox
        )

        self.radioBtnsLayout = QtWidgets.QVBoxLayout()
        self.radioBtnsLayout.setObjectName("radioBtnsLayout")
        self.radioBtnsLayout.setContentsMargins(-1, -1, -1, 10)

        self.radioButton_one = QtWidgets.QRadioButton(self.restrictionForm)
        self.radioButton_one.setObjectName("radioButton_one")
        self.radioButton_one.setEnabled(False)
        self.radioButton_one.setChecked(True)
        self.radioBtnsLayout.addWidget(self.radioButton_one)

        self.radioButton_multiple = QtWidgets.QRadioButton(self.restrictionForm)
        self.radioButton_multiple.setObjectName("radioButton_multiple")
        self.radioButton_multiple.setEnabled(False)
        self.radioBtnsLayout.addWidget(self.radioButton_multiple)

        self.typeFormLayout.setLayout(
            1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.radioBtnsLayout
        )
        self.restrictionFormLayout.addLayout(self.typeFormLayout)

        self.nameLayout = QtWidgets.QFormLayout()
        self.nameLabel = QtWidgets.QLabel("Название:", self.restrictionForm)
        self.restrictionNameEdit = QtWidgets.QLineEdit(self.restrictionForm)
        self.restrictionNameEdit.setEnabled(False)
        self.nameLayout.addRow(self.nameLabel, self.restrictionNameEdit)

        self.commentLabel = QtWidgets.QLabel("Комментарий:", self.restrictionForm)
        self.restrictionCommentEdit = QtWidgets.QLineEdit(self.restrictionForm)
        self.restrictionCommentEdit.setEnabled(False)
        self.nameLayout.addRow(self.commentLabel, self.restrictionCommentEdit)
        self.restrictionFormLayout.addLayout(self.nameLayout)

        icon = QIcon()
        icon.addFile(
            ":/plugins/qgis_route_planner/cross_white",
            QSize(), QIcon.Mode.Normal, QIcon.State.Off
        )

        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")

        self.label = QtWidgets.QLabel(self.restrictionForm)
        self.label.setObjectName("label")
        self.formLayout.setWidget(
            0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label
        )
        self.startPointLayout = QtWidgets.QHBoxLayout()
        self.startPointEdit = QtWidgets.QLineEdit(self.restrictionForm)
        self.startPointEdit.setEnabled(False)
        self.startPointEdit.setReadOnly(True)
        self.startPointLayout.addWidget(self.startPointEdit)
        self.chooseStartPointButton = QtWidgets.QPushButton("Выбрать", self.restrictionForm)
        self.chooseStartPointButton.setEnabled(False)
        self.startPointLayout.addWidget(self.chooseStartPointButton)
        self.clearStartButton = QtWidgets.QPushButton(self.restrictionForm)
        self.clearStartButton.setEnabled(False)
        self.clearStartButton.setIcon(icon)
        self.startPointLayout.addWidget(self.clearStartButton)
        self.formLayout.setLayout(
            0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.startPointLayout
        )

        self.label_3 = QtWidgets.QLabel(self.restrictionForm)
        self.label_3.setObjectName("label_3")
        self.label_3.setWordWrap(True)
        self.formLayout.setWidget(
            1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_3
        )
        self.midPointsLayoutWidget = QtWidgets.QWidget()
        self.midPointsLayout = QtWidgets.QHBoxLayout(self.midPointsLayoutWidget)
        self.midPointsLayout.setContentsMargins(0, 0, 0, 0)
        self.midPointsListView = QtWidgets.QListWidget(self.restrictionForm)
        self.midPointsListView.setEnabled(False)
        self.midPointsListView.setMaximumHeight(100)
        self.midPointsListView.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn
        )
        self.midPointsLayout.addWidget(self.midPointsListView)
        self.midPointsButtonsLayout = QtWidgets.QVBoxLayout()
        self.chooseMidPointsButton = QtWidgets.QPushButton("Выбрать", self.restrictionForm)
        self.chooseMidPointsButton.setEnabled(False)
        self.midPointsButtonsLayout.addWidget(self.chooseMidPointsButton)
        self.clearMidListButton = QtWidgets.QPushButton(self.restrictionForm)
        self.clearMidListButton.setEnabled(False)
        self.clearMidListButton.setIcon(icon)
        self.midPointsButtonsLayout.addWidget(self.clearMidListButton)
        self.midPointsLayout.addLayout(self.midPointsButtonsLayout)
        self.formLayout.setWidget(
            1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.midPointsLayoutWidget
        )

        self.label_4 = QtWidgets.QLabel(self.restrictionForm)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(
            2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_4
        )
        self.endPointLayout = QtWidgets.QHBoxLayout()
        self.endPointEdit = QtWidgets.QLineEdit(self.restrictionForm)
        self.endPointEdit.setEnabled(False)
        self.endPointEdit.setReadOnly(True)
        self.endPointLayout.addWidget(self.endPointEdit)
        self.chooseEndPointButton = QtWidgets.QPushButton("Выбрать", self.restrictionForm)
        self.chooseEndPointButton.setEnabled(False)
        self.endPointLayout.addWidget(self.chooseEndPointButton)
        self.clearEndButton = QtWidgets.QPushButton(self.restrictionForm)
        self.clearEndButton.setEnabled(False)
        self.clearEndButton.setIcon(icon)
        self.endPointLayout.addWidget(self.clearEndButton)
        self.formLayout.setLayout(
            2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.endPointLayout
        )

        self.restrictionFormLayout.addLayout(self.formLayout)

        # Специфичные параметры
        self.stackedWidget = QtWidgets.QStackedWidget(self.restrictionForm)
        self.stackedWidget.setObjectName("stackedWidget")
        self.pageSimple = QtWidgets.QWidget()
        self.stackedWidget.addWidget(self.pageSimple)
        self.pageDimension = self.__build_dimension_page()
        self.stackedWidget.addWidget(self.pageDimension)
        self.pageTemporary = self.__build_temporary_page()
        self.stackedWidget.addWidget(self.pageTemporary)
        self.restrictionFormLayout.addWidget(self.stackedWidget)

        self.restrictionFormLayout.addItem(
            QtWidgets.QSpacerItem(
                20, 40,
                QtWidgets.QSizePolicy.Policy.Minimum,
                QtWidgets.QSizePolicy.Policy.Expanding
            )
        )

        self.dialogButtonsLayout = QtWidgets.QHBoxLayout()
        self.saveRestrictionButton = QtWidgets.QPushButton("Сохранить", self.restrictionForm)
        self.saveRestrictionButton.setEnabled(False)
        self.dialogButtonsLayout.addWidget(self.saveRestrictionButton)
        self.cancelRestrictionEditButton = QtWidgets.QPushButton("Отмена", self.restrictionForm)
        self.cancelRestrictionEditButton.setEnabled(False)
        self.dialogButtonsLayout.addWidget(self.cancelRestrictionEditButton)
        self.restrictionFormLayout.addLayout(self.dialogButtonsLayout)

        self.horizontalLayout.addWidget(self.restrictionForm)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        _t = QtCore.QCoreApplication.translate
        self.setWindowTitle(_t("RestrictionDialog", "Настройки ограничений"))
        self.createRestrictionButton.setText(_t("RestrictionDialog", "Новое ограничение"))
        self.deleteRestrictionButton.setText(_t("RestrictionDialog", "Удалить"))
        self.editRestrictionButton.setText(_t("RestrictionDialog", "Изменить"))
        self.label_2.setText(_t("RestrictionDialog", "Тип:"))
        self.radioButton_one.setText(_t("RestrictionDialog", "Одна точка"))
        self.radioButton_multiple.setText(_t("RestrictionDialog", "Несколько точек"))
        self.label.setText(_t("RestrictionDialog", "Начальная точка:"))
        self.label_3.setText(_t("RestrictionDialog", "Промежуточные точки:"))
        self.label_4.setText(_t("RestrictionDialog", "Конечная точка:"))
        self.clearStartButton.setText("✕")
        self.clearMidListButton.setText("✕")
        self.clearEndButton.setText("✕")

    def __build_dimension_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(page)
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
        layout.addRow("Макс. высота:", self.dimHeightSpin)
        layout.addRow("Макс. ширина:", self.dimWidthSpin)
        layout.addRow("Макс. длина:", self.dimLengthSpin)
        layout.addRow("Макс. вес:", self.dimWeightSpin)
        return page

    def __build_temporary_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(page)
        self.tmpDateFrom = QtWidgets.QDateTimeEdit()
        self.tmpDateFrom.setCalendarPopup(True)
        self.tmpDateFrom.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.tmpDateFrom.setEnabled(False)
        self.tmpDateTo = QtWidgets.QDateTimeEdit()
        self.tmpDateTo.setCalendarPopup(True)
        self.tmpDateTo.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.tmpDateTo.setEnabled(False)
        layout.addRow("Начало действия:", self.tmpDateFrom)
        layout.addRow("Конец действия:", self.tmpDateTo)
        return page

    def __on_type_changed(self, index: int):
        rt = self.restrictionTypeComboBox.itemData(index)
        page_map = {
            RestrictionType.SIMPLE: 0,
            RestrictionType.DIMENSION: 1,
            RestrictionType.TEMPORARY: 2,
        }
        self.stackedWidget.setCurrentIndex(page_map.get(rt, 0))

    def __on_points_count_changed(self):
        is_single = self.radioButton_one.isChecked()
        self.midPointsLayoutWidget.setVisible(not is_single)
        self.label_3.setVisible(not is_single)
        self.endPointEdit.setVisible(not is_single)
        self.chooseEndPointButton.setVisible(not is_single)
        self.clearEndButton.setVisible(not is_single)
        self.label_4.setVisible(not is_single)

    def __on_list_selection_changed(self):
        self.__controller.on_restriction_selected(self.get_selected_restriction_id())

    def __on_save_clicked(self):
        self.__controller.on_save_restriction(self.collect_form_data())

    def __on_select_point_clicked(self, point_type: str):
        self.__current_point_type = point_type
        self.__controller.on_select_point_on_map()
        self.hide()

    def __clear_point(self, point_type: str):
        if point_type == "start":
            self.startPointEdit.clear()
            self.startPointEdit.setProperty("node_id", None)
        elif point_type == "end":
            self.endPointEdit.clear()
            self.endPointEdit.setProperty("node_id", None)

    def __clear_points(self, point_type: str):
        if point_type == "mid":
            self.midPointsListView.clear()

    def collect_form_data(self) -> dict:
        data = {
            "name": self.restrictionNameEdit.text().strip(),
            "comment": self.restrictionCommentEdit.text().strip(),
            "restriction_type": self.get_current_type(),
            "start_node": self.startPointEdit.property("node_id"),
            "mid_nodes": [],
            "end_node": self.endPointEdit.property("node_id"),
        }
        for i in range(self.midPointsListView.count()):
            item = self.midPointsListView.item(i)
            data["mid_nodes"].append(item.data(QtCore.Qt.ItemDataRole.UserRole))

        rt = data["restriction_type"]
        if rt == RestrictionType.DIMENSION:
            data["dimension_values"] = {
                "height": self.dimHeightSpin.value(),
                "width": self.dimWidthSpin.value(),
                "length": self.dimLengthSpin.value(),
                "weight": self.dimWeightSpin.value(),
            }
        elif rt == RestrictionType.TEMPORARY:
            data["temporary_dates"] = {
                "from": self.tmpDateFrom.dateTime().toString("yyyy-MM-dd HH:mm"),
                "to": self.tmpDateTo.dateTime().toString("yyyy-MM-dd HH:mm"),
            }
        return data

    def get_selected_restriction_id(self) -> int | None:
        items = self.restrictionListWidget.selectedItems()
        return items[0].data(QtCore.Qt.ItemDataRole.UserRole) if items else None

    def get_current_type(self) -> RestrictionType:
        return self.restrictionTypeComboBox.currentData()

    def set_restrictions_list(self, restrictions: list[dict]):
        self.restrictionListWidget.clear()
        for r in restrictions:
            label = f"{r.get('name', '—')} [{r.get('restriction_type_name', '')}]"
            item = QtWidgets.QListWidgetItem(label)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, r.get("id"))
            self.restrictionListWidget.addItem(item)

    def set_form_state(self, mode: FormMode):
        is_editing = mode in (FormMode.EDIT, FormMode.CREATE)
        has_selection = mode == FormMode.VIEW

        for w in (
                self.restrictionTypeComboBox,
                self.restrictionNameEdit,
                self.restrictionCommentEdit,
                self.radioButton_one,
                self.radioButton_multiple,
                self.chooseStartPointButton,
                self.chooseMidPointsButton,
                self.chooseEndPointButton,
                self.clearStartButton,
                self.clearMidListButton,
                self.clearEndButton,
                self.saveRestrictionButton,
                self.cancelRestrictionEditButton,
                self.dimHeightSpin,
                self.dimWidthSpin,
                self.dimLengthSpin,
                self.dimWeightSpin,
                self.tmpDateFrom,
                self.tmpDateTo,
        ):
            w.setEnabled(is_editing)

        self.editRestrictionButton.setEnabled(has_selection)
        self.deleteRestrictionButton.setEnabled(has_selection)

    def set_list_buttons_enabled(self, enabled: bool):
        self.editRestrictionButton.setEnabled(enabled)
        self.deleteRestrictionButton.setEnabled(enabled)

    def clear_form(self):
        self.restrictionNameEdit.clear()
        self.restrictionCommentEdit.clear()
        self.startPointEdit.clear()
        self.startPointEdit.setProperty("node_id", None)
        self.midPointsListView.clear()
        self.endPointEdit.clear()
        self.endPointEdit.setProperty("node_id", None)
        self.dimHeightSpin.setValue(0)
        self.dimWidthSpin.setValue(0)
        self.dimLengthSpin.setValue(0)
        self.dimWeightSpin.setValue(0)
        now = QDateTime.currentDateTime()
        self.tmpDateFrom.setDateTime(now)
        self.tmpDateTo.setDateTime(now.addDays(7))
        self.restrictionTypeComboBox.setCurrentIndex(0)

    def load_restriction_to_form(self, data: dict):
        self.restrictionNameEdit.setText(data.get("name", ""))
        self.restrictionCommentEdit.setText(data.get("comment", ""))

        type_id = data.get("restriction_type_id", 1)
        rt = {1: RestrictionType.SIMPLE,
              2: RestrictionType.DIMENSION,
              3: RestrictionType.TEMPORARY}.get(type_id, RestrictionType.SIMPLE)
        idx = self.restrictionTypeComboBox.findData(rt)
        if idx >= 0:
            self.restrictionTypeComboBox.setCurrentIndex(idx)

        self.startPointEdit.clear()
        self.startPointEdit.setProperty("node_id", None)
        self.midPointsListView.clear()
        self.endPointEdit.clear()
        self.endPointEdit.setProperty("node_id", None)

        node_id = data.get("node_id")
        if node_id:
            self.startPointEdit.setText(f"Node {node_id}")
            self.startPointEdit.setProperty("node_id", node_id)
            self.radioButton_one.setChecked(True)

        value_text = data.get("value_text", "")
        if rt == RestrictionType.DIMENSION and value_text:
            pairs = dict(p.split("=", 1) for p in value_text.split(";") if "=" in p)
            self.dimHeightSpin.setValue(float(pairs.get("height", 0)))
            self.dimWidthSpin.setValue(float(pairs.get("width", 0)))
            self.dimLengthSpin.setValue(float(pairs.get("length", 0)))
            self.dimWeightSpin.setValue(float(pairs.get("weight", 0)))
        elif rt == RestrictionType.TEMPORARY and value_text:
            pairs = dict(p.split("=", 1) for p in value_text.split(";") if "=" in p)
            fmt = "yyyy-MM-dd HH:mm"
            if "from" in pairs:
                self.tmpDateFrom.setDateTime(QDateTime.fromString(pairs["from"], fmt))
            if "to" in pairs:
                self.tmpDateTo.setDateTime(QDateTime.fromString(pairs["to"], fmt))

    def on_point_selected_callback(self, point, node_id):
        if self.__current_point_type == "start":
            self.startPointEdit.setText(
                f"Node {node_id} ({point.x():.5f}, {point.y():.5f})"
            )
            self.startPointEdit.setProperty("node_id", node_id)
        elif self.__current_point_type == "mid":
            item = QtWidgets.QListWidgetItem(
                f"Node {node_id} ({point.x():.5f}, {point.y():.5f})"
            )
            item.setData(QtCore.Qt.ItemDataRole.UserRole, node_id)
            self.midPointsListView.addItem(item)
        elif self.__current_point_type == "end":
            self.endPointEdit.setText(
                f"Node {node_id} ({point.x():.5f}, {point.y():.5f})"
            )
            self.endPointEdit.setProperty("node_id", node_id)
        self.show()

    def show_warning_message(self, message: str):
        QtWidgets.QMessageBox.warning(self, "Предупреждение", message, QtWidgets.QMessageBox.Ok)

    def show_info_message(self, message: str):
        QtWidgets.QMessageBox.information(self, "Информация", message, QtWidgets.QMessageBox.Ok)

    def show_critical_message(self, message: str):
        QtWidgets.QMessageBox.critical(self, "Ошибка", message, QtWidgets.QMessageBox.Ok)

    def ask_confirmation(self, message: str) -> bool:
        reply = QtWidgets.QMessageBox.question(
            self, "Подтверждение", message,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        return reply == QtWidgets.QMessageBox.Yes