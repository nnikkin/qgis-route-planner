# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..controllers import RestrictionDialogController
    from ..data.models import RestrictionModel

from qgis.PyQt import QtCore, QtWidgets
from qgis.PyQt.QtCore import QDateTime, QObject, QSize
from qgis.PyQt.QtGui import QIcon

from .message_box_mixin import MessageBoxMixin
from ..data.models import RestrictionType
from ..data.route import RestrictionRecord
from ..utils import FormMode


class RestrictionDialog(QtWidgets.QDialog, MessageBoxMixin):
    """ Диалог организации ограничений """

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
        self.restrictionNameEdit.textChanged.connect(self.__controller.change_name_value)
        self.restrictionCommentEdit.textChanged.connect(self.__controller.change_comment_value)

        self.__controller.show_error.connect(self.show_critical_message)
        self.__controller.show_warning.connect(self.show_warning_message)
        self.__controller.show_info.connect(self.show_info_message)
        self.__controller.open_requested.connect(self.open)
        self.__controller.point_selected.connect(self.on_point_selected_callback)

        self.__model.restriction_type_changed.connect(self.__on_restriction_type_value_changed)
        self.__model.name_changed.connect(self.__on_name_value_changed)
        self.__model.comment_changed.connect(self.__on_comment_value_changed)
        self.__model.point_changed.connect(self.__on_start_point_value_changed)
        self.__model.valid_from_changed.connect(self.__on_valid_from_value_changed)
        self.__model.valid_to_changed.connect(self.__on_valid_to_value_changed)
        self.__model.max_height_changed.connect(self.__on_max_height_value_changed)
        self.__model.max_width_changed.connect(self.__on_max_width_value_changed)
        self.__model.max_weight_changed.connect(self.__on_max_weight_value_changed)
        self.__model.restrictions_changed.connect(self.set_restrictions_list)
        self.__model.current_restriction_id_changed.connect(self.__on_current_id_changed)
        self.__model.editing_mode_changed.connect(self.set_form_state)

    def __connect_ui_signals(self):
        """ Сигналы от UI-элементов к контроллеру"""
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

        self.choosePointButton.clicked.connect(
            lambda: self.__on_select_point_clicked("start")
        )

        self.clearPointFieldButton.clicked.connect(lambda: self.__clear_point("start"))

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
        for rt in RestrictionType:
            self.restrictionTypeComboBox.addItem(rt.value, rt)
        self.restrictionTypeComboBox.setCurrentIndex(0)
        self.restrictionTypeComboBox.setEnabled(False)
        self.typeFormLayout.setWidget(
            0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.restrictionTypeComboBox
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
        self.pointSelectLayout = QtWidgets.QHBoxLayout()

        self.pointEdit = QtWidgets.QLineEdit(self.restrictionForm)
        self.pointEdit.setEnabled(False)
        self.pointEdit.setReadOnly(True)
        self.pointSelectLayout.addWidget(self.pointEdit)

        self.choosePointButton = QtWidgets.QPushButton("Выбрать", self.restrictionForm)
        self.choosePointButton.setEnabled(False)
        self.pointSelectLayout.addWidget(self.choosePointButton)

        self.clearPointFieldButton = QtWidgets.QPushButton(self.restrictionForm)
        self.clearPointFieldButton.setEnabled(False)
        self.clearPointFieldButton.setIcon(icon)
        self.pointSelectLayout.addWidget(self.clearPointFieldButton)
        self.formLayout.setLayout(
            0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.pointSelectLayout
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
        self.label.setText(_t("RestrictionDialog", "Точка:"))
        self.clearPointFieldButton.setText("✕")

    def __build_dimension_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(page)

        self.dimHeightSpin = QtWidgets.QDoubleSpinBox()
        self.dimHeightSpin.setSuffix(" м")
        self.dimHeightSpin.setMaximum(99.0)
        self.dimHeightSpin.setEnabled(False)
        self.dimHeightSpin.valueChanged.connect(
            self.__controller.change_max_height_value
        )

        self.dimWidthSpin = QtWidgets.QDoubleSpinBox()
        self.dimWidthSpin.setSuffix(" м")
        self.dimWidthSpin.setMaximum(99.0)
        self.dimWidthSpin.setEnabled(False)
        self.dimWidthSpin.valueChanged.connect(
            self.__controller.change_max_width_value
        )

        self.dimWeightSpin = QtWidgets.QDoubleSpinBox()
        self.dimWeightSpin.setSuffix(" т")
        self.dimWeightSpin.setMaximum(999.0)
        self.dimWeightSpin.setEnabled(False)
        self.dimWeightSpin.valueChanged.connect(
            self.__controller.change_max_weight_value
        )

        layout.addRow("Макс. высота:", self.dimHeightSpin)
        layout.addRow("Макс. ширина:", self.dimWidthSpin)
        layout.addRow("Макс. вес:", self.dimWeightSpin)
        return page

    def __build_temporary_page(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(page)

        self.tmpDateFrom = QtWidgets.QDateTimeEdit()
        self.tmpDateFrom.setCalendarPopup(True)
        self.tmpDateFrom.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.tmpDateFrom.setEnabled(False)
        self.tmpDateFrom.dateTimeChanged.connect(
            self.__controller.change_valid_from_value
        )

        self.tmpDateTo = QtWidgets.QDateTimeEdit()
        self.tmpDateTo.setCalendarPopup(True)
        self.tmpDateTo.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.tmpDateTo.setEnabled(False)
        self.tmpDateTo.dateTimeChanged.connect(
            self.__controller.change_valid_to_value
        )

        layout.addRow("Начало действия:", self.tmpDateFrom)
        layout.addRow("Конец действия:", self.tmpDateTo)
        return page

    def __on_type_changed(self, index: int):
        rt = self.restrictionTypeComboBox.itemData(index)
        self.__set_type_page(rt)
        self.__controller.change_restriction_type_value(rt)

    def __set_type_page(self, rt: RestrictionType):
        page_map = {
            RestrictionType.SIMPLE: 0,
            RestrictionType.DIMENSION: 1,
            RestrictionType.TEMPORARY: 2,
        }
        self.stackedWidget.setCurrentIndex(page_map.get(rt, 0))

    def __on_list_selection_changed(self):
        self.__controller.on_restriction_selected(self.get_selected_restriction_id())

    def __on_save_clicked(self):
        self.__controller.on_save_restriction()

    def __on_select_point_clicked(self, point_type: str):
        self.__current_point_type = point_type
        self.__controller.on_select_point_on_map()
        self.hide()

    def __clear_point(self, point_type: str):
        self.__controller.change_point_value(None, None)


    def get_selected_restriction_id(self) -> int | None:
        items = self.restrictionListWidget.selectedItems()
        return items[0].data(QtCore.Qt.ItemDataRole.UserRole) if items else None

    def set_restrictions_list(self, restrictions: list[RestrictionRecord]):
        self.restrictionListWidget.blockSignals(True)
        self.restrictionListWidget.clear()
        for r in restrictions:
            if isinstance(r, dict):
                restriction_id = r.get("id")
                name = r.get("name", "—")
                type_name = r.get(
                    "restriction_type_name",
                    RestrictionRecord.id_to_type_name(r.get("restriction_type_id", 1))
                )
            else:
                restriction_id = r.id
                name = r.name or "—"
                type_name = RestrictionRecord.id_to_type_name(r.restriction_type_id)
            label = f"{name} [{type_name}]"
            item = QtWidgets.QListWidgetItem(label)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, restriction_id)
            self.restrictionListWidget.addItem(item)
            if restriction_id == self.__model.current_restriction_id:
                self.restrictionListWidget.setCurrentItem(item)
        self.restrictionListWidget.blockSignals(False)

    def set_form_state(self, mode: FormMode):
        is_editing = mode in (FormMode.EDIT, FormMode.CREATE)
        has_selection = self.__model.current_restriction_id is not None

        for w in (
                self.restrictionTypeComboBox,
                self.restrictionNameEdit,
                self.restrictionCommentEdit,
                self.choosePointButton,
                self.clearPointFieldButton,
                self.saveRestrictionButton,
                self.cancelRestrictionEditButton,
                self.dimHeightSpin,
                self.dimWidthSpin,
                self.dimWeightSpin,
                self.tmpDateFrom,
                self.tmpDateTo,
        ):
            w.setEnabled(is_editing)

        self.createRestrictionButton.setEnabled(not is_editing)
        self.restrictionListWidget.setEnabled(not is_editing)
        self.editRestrictionButton.setEnabled(has_selection and not is_editing)
        self.deleteRestrictionButton.setEnabled(has_selection and not is_editing)

    def set_list_buttons_enabled(self, enabled: bool):
        self.editRestrictionButton.setEnabled(enabled)
        self.deleteRestrictionButton.setEnabled(enabled)

    def clear_form(self):
        self.restrictionNameEdit.clear()
        self.restrictionCommentEdit.clear()
        self.pointEdit.clear()
        self.pointEdit.setProperty("node_id", None)
        self.dimHeightSpin.setValue(0)
        self.dimWidthSpin.setValue(0)
        self.dimWeightSpin.setValue(0)
        now = QDateTime.currentDateTime()
        self.tmpDateFrom.setDateTime(now)
        self.tmpDateTo.setDateTime(now.addDays(7))
        self.restrictionTypeComboBox.setCurrentIndex(0)

    def __on_current_id_changed(self, restriction_id: int | None):
        self.set_list_buttons_enabled(restriction_id is not None)
        if restriction_id is None:
            self.restrictionListWidget.clearSelection()

    def __on_restriction_type_value_changed(self, value: RestrictionType):
        self.__set_combo_value(self.restrictionTypeComboBox, value)
        self.__set_type_page(value)

    def __on_name_value_changed(self, value: str):
        self.__set_line_edit_value(self.restrictionNameEdit, value)

    def __on_comment_value_changed(self, value: str):
        self.__set_line_edit_value(self.restrictionCommentEdit, value)

    def __on_start_point_value_changed(self, value):
        self.__set_point_edit_value(self.pointEdit, value)

    def __on_valid_from_value_changed(self, value):
        self.__set_datetime_value(self.tmpDateFrom, value)

    def __on_valid_to_value_changed(self, value):
        self.__set_datetime_value(self.tmpDateTo, value)

    def __on_max_height_value_changed(self, value: float):
        self.__set_spin_value(self.dimHeightSpin, value)

    def __on_max_width_value_changed(self, value: float):
        self.__set_spin_value(self.dimWidthSpin, value)

    def __on_max_weight_value_changed(self, value: float):
        self.__set_spin_value(self.dimWeightSpin, value)

    @staticmethod
    def __set_line_edit_value(widget, value: str):
        widget.blockSignals(True)
        widget.setText(value or "")
        widget.blockSignals(False)

    @staticmethod
    def __set_spin_value(widget, value: float):
        widget.blockSignals(True)
        widget.setValue(float(value or 0))
        widget.blockSignals(False)

    @staticmethod
    def __set_combo_value(widget, value):
        widget.blockSignals(True)
        index = widget.findData(value)
        if index >= 0:
            widget.setCurrentIndex(index)
        widget.blockSignals(False)

    @staticmethod
    def __set_datetime_value(widget, value):
        widget.blockSignals(True)
        if value:
            if hasattr(value, "toString"):
                widget.setDateTime(value)
            else:
                dt_value = QDateTime.fromString(str(value), "yyyy-MM-dd HH:mm")
                if dt_value.isValid():
                    widget.setDateTime(dt_value)
        else:
            widget.setDateTime(QDateTime.currentDateTime())
        widget.blockSignals(False)

    def __set_point_edit_value(self, widget, value):
        point, node_id = self.__unpack_point_data(value)
        widget.blockSignals(True)
        widget.setText(self.__point_label(point, node_id) if node_id is not None else "")
        widget.setProperty("node_id", node_id)
        widget.blockSignals(False)

    @staticmethod
    def __unpack_point_data(value):
        if value is None:
            return None, None
        if isinstance(value, tuple) and len(value) >= 2:
            return value[0], value[1]
        if isinstance(value, dict):
            return value.get("point"), value.get("node_id")
        return value, None

    @staticmethod
    def __point_label(point, node_id):
        if node_id is None:
            return ""
        if point is None:
            return f"Node {node_id}"
        return f"Node {node_id} ({point.x():.5f}, {point.y():.5f})"

    def on_point_selected_callback(self, point, node_id):
        self.__controller.change_point_value(point, node_id)
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

    def closeEvent(self, event):
        """ Обработчик закрытия окна """
        self.__controller.on_cancel_edit()
