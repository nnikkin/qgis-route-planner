# -*- coding: utf-8 -*-
from qgis.PyQt import QtCore, QtWidgets
from qgis.PyQt.QtGui import QRegExpValidator
from qgis.PyQt.QtCore import QRegExp
from qgis.PyQt.QtWidgets import QMessageBox

from qgis_route_planner.views.base_qdialog import BaseQDialog


class DbConnectionSetupDialog(BaseQDialog):
    """Диалоговое окно подключения к БД"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi()

    def setupUi(self):
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
        self.buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel |
                                          QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
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

    def closeEvent(self, event):
        close_question = QMessageBox.question(
            self,
            "Внимание",
            "Для продолжения требуется настроить подключение.\nВы уверены, что хотите закрыть мастер подключения?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if close_question == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()