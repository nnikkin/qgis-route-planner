# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from db_init_controller import DbInitController

from qgis.PyQt import QtWidgets
from qgis.PyQt.QtGui import QRegExpValidator
from qgis.PyQt.QtCore import Qt, QRegExp, QObject, QMetaObject, QCoreApplication, pyqtSlot

from qgis_route_planner.presentation import MessageBoxMixin
from db_config_model import DbConfigModel

class ConnectionConfigDialog(QtWidgets.QDialog, MessageBoxMixin):
    """ Диалоговое окно подключения к БД """

    def __init__(
            self,
            model: DbConfigModel,
            controller: DbInitController,
            parent: QObject = None
    ):
        super().__init__(parent)

        self.__model = model
        self.__controller = controller

        self.__step_finished = False

        self.__schemas = []

        self.__setupUi()

    def __connect(self):
        self.host_edit.textChanged.connect(self.__controller.change_host_value)
        self.port_edit.textChanged.connect(self.__controller.change_port_value)
        self.username_edit.textChanged.connect(self.__controller.change_username_value)
        self.password_edit.textChanged.connect(self.__controller.change_password_value)
        self.database_edit.textChanged.connect(self.__controller.change_database_value)
        self.schema_comboBox.currentTextChanged.connect(self.__controller.change_schema_value)
        self.check_con_button.clicked.connect(self.__fill_combobox)
        self.buttonBox.accepted.connect(self.__on_accept)
        self.buttonBox.rejected.connect(self.close)

        self.__model.host_changed.connect(self.__on_host_value_changed)
        self.__model.port_changed.connect(self.__on_port_value_changed)
        self.__model.password_changed.connect(self.__on_password_value_changed)
        self.__model.username_changed.connect(self.__on_username_value_changed)
        self.__model.database_changed.connect(self.__on_database_value_changed)
        self.__model.schema_changed.connect(self.__on_schema_value_changed)
        self.__model.any_field_changed.connect(self.__update_check_button)

        self.__controller.connection_failed.connect(self.__on_connection_failed)

    def __setupUi(self):
        self.setObjectName("DbConnectionSetupDialog")
        self.resize(350, 250)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)

        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")

        self.formLayout_3 = QtWidgets.QFormLayout()
        self.formLayout_3.setObjectName("formLayout_3")

        self.label_12 = QtWidgets.QLabel(self)
        self.label_12.setObjectName("label_12")
        self.formLayout_3.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_12)

        self.host_edit = QtWidgets.QLineEdit(self)
        self.host_edit.setMaxLength(200)
        self.host_edit.setClearButtonEnabled(True)
        self.host_edit.setObjectName("host_edit")
        self.formLayout_3.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.host_edit)

        self.label_13 = QtWidgets.QLabel(self)
        self.label_13.setObjectName("label_13")
        self.formLayout_3.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_13)

        self.port_edit = QtWidgets.QLineEdit(self)
        self.port_edit.setMaxLength(6)
        self.port_edit.setClearButtonEnabled(True)
        self.port_edit.setObjectName("port_edit")
        self.port_edit.setValidator(QRegExpValidator(QRegExp("[0-9]{,5}"), self.port_edit))
        self.formLayout_3.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.port_edit)

        self.label_15 = QtWidgets.QLabel(self)
        self.label_15.setObjectName("label_15")
        self.formLayout_3.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_15)

        self.username_edit = QtWidgets.QLineEdit(self)
        self.username_edit.setMaxLength(50)
        self.username_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Normal)
        self.username_edit.setClearButtonEnabled(True)
        self.username_edit.setObjectName("username_edit")
        self.formLayout_3.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.username_edit)

        self.label_16 = QtWidgets.QLabel(self)
        self.label_16.setObjectName("label_16")
        self.formLayout_3.setWidget(3, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_16)

        self.password_edit = QtWidgets.QLineEdit(self)
        self.password_edit.setMaxLength(50)
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("")
        self.password_edit.setClearButtonEnabled(True)
        self.password_edit.setObjectName("password_edit")
        self.formLayout_3.setWidget(3, QtWidgets.QFormLayout.ItemRole.FieldRole, self.password_edit)

        self.check_con_button = QtWidgets.QPushButton(self)
        self.check_con_button.setEnabled(False)
        self.check_con_button.setObjectName("check_con_button")
        self.formLayout_3.setWidget(5, QtWidgets.QFormLayout.ItemRole.FieldRole, self.check_con_button)

        self.label_2 = QtWidgets.QLabel(self)
        self.label_2.setObjectName("label_2")
        self.formLayout_3.setWidget(6, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_2)

        self.schema_comboBox = QtWidgets.QComboBox(self)
        self.schema_comboBox.setEnabled(False)
        self.schema_comboBox.setEditable(False)
        self.schema_comboBox.setObjectName("schema_comboBox")
        self.formLayout_3.setWidget(6, QtWidgets.QFormLayout.ItemRole.FieldRole, self.schema_comboBox)

        self.label_3 = QtWidgets.QLabel(self)
        self.label_3.setObjectName("label_3")
        self.formLayout_3.setWidget(4, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_3)

        self.database_edit = QtWidgets.QLineEdit(self)
        self.database_edit.setMaxLength(100)
        self.database_edit.setObjectName("database_edit")
        self.database_edit.setClearButtonEnabled(True)
        self.formLayout_3.setWidget(4, QtWidgets.QFormLayout.ItemRole.FieldRole, self.database_edit)

        self.gridLayout.addLayout(self.formLayout_3, 0, 0, 1, 1)

        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel |
                                          QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.__retranslateUi()
        QMetaObject.connectSlotsByName(self)
        self.__connect()

    def __retranslateUi(self):
        _translate = QCoreApplication.translate
        self.setWindowTitle(_translate("Dialog", "Шаг 1: настройка подключения к БД"))
        self.label_12.setText(_translate("Dialog", "Адрес:"))
        self.host_edit.setPlaceholderText(_translate("Dialog", "Например, localhost"))
        self.label_13.setText(_translate("Dialog", "Порт:"))
        self.port_edit.setPlaceholderText(_translate("Dialog", "Например, 5432"))
        self.label_15.setText(_translate("Dialog", "Пользователь:"))
        self.username_edit.setPlaceholderText(_translate("Dialog", "Например, postgres"))
        self.label_16.setText(_translate("Dialog", "Пароль:"))
        self.check_con_button.setText(_translate("Dialog", "Проверить подключение"))
        self.label_2.setText(_translate("Dialog", "Схема:"))
        self.label_3.setText(_translate("Dialog", "База данных:"))

    def showEvent(self, event, **kwargs):
        super().showEvent(event)
        self.__step_finished = False

    def closeEvent(self, event, **kwargs):
        if not self.__step_finished:
            close_dialog = self._show_question(
                "Для продолжения требуется настроить подключение.\nВы уверены, что хотите закрыть мастер подключения?"
            )

            if close_dialog:
                self.__controller.initialization_cancelled()
                event.accept()
            else:
                event.ignore()

    def __update_check_button(self):
        self.check_con_button.setEnabled(self.__controller.validate_values_for_schema())
        self.schema_comboBox.blockSignals(True)
        self.schema_comboBox.clear()
        self.schema_comboBox.blockSignals(False)
        self.__controller.change_schema_value("")
        self.schema_comboBox.setEnabled(False)

    @pyqtSlot(str)
    def __on_host_value_changed(self, value):
        self.host_edit.setText(value)

    @pyqtSlot(str)
    def __on_port_value_changed(self, value):
        self.port_edit.setText(value)

    @pyqtSlot(str)
    def __on_username_value_changed(self, value):
        self.username_edit.setText(value)

    @pyqtSlot(str)
    def __on_password_value_changed(self, value):
        self.password_edit.setText(value)

    @pyqtSlot(str)
    def __on_database_value_changed(self, value):
        self.database_edit.setText(value)

    @pyqtSlot(str)
    def __on_schema_value_changed(self, value):
        index = self.schema_comboBox.findText(value)
        if index >= 0:
            self.schema_comboBox.setCurrentIndex(index)

    @pyqtSlot(str)
    def __on_connection_failed(self, message: str):
        self._show_critical("Ошибка подключения: " + message)
        self.check_con_button.setEnabled(True)

    def __on_accept(self):
        if not self.__controller.validate_connection_step():
            self._show_info("Заполните параметры подключения, нажмите \"Проверить подключение\" и выберите схему.")
            return

        self.__step_finished = True
        self.accept()
        self.__controller.connection_step_finish()

    def __fill_combobox(self):
        self.schema_comboBox.setEnabled(False)
        self.check_con_button.setEnabled(False)
        self.schema_comboBox.clear()

        self.__controller.request_connection()
        schemas = self.__controller.get_schemas()
        if not schemas:
            self.check_con_button.setEnabled(True)
            return

        self.schema_comboBox.addItems(schemas)
        self.schema_comboBox.setCurrentIndex(0)

        self.schema_comboBox.setEnabled(True)
        self.check_con_button.setEnabled(True)
