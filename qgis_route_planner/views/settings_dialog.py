# -*- coding: utf-8 -*-

from qgis.PyQt import QtCore, QtWidgets
from qgis.PyQt.QtWidgets import QDialog, QMessageBox, QListWidgetItem
from qgis.PyQt.QtCore import QObject, pyqtSlot

from ..controllers import SettingsWindowController
from ..data.models import SettingsModel
from ..data.vehicle import VehicleProfile, VehicleType


class SettingsDialog(QDialog):
    """Окно настроек плагина"""

    def __init__(
            self,
            model: SettingsModel,
            controller: SettingsWindowController = None,
            parent: QObject = None
    ):
        super().__init__(parent)

        self.__controller: SettingsWindowController = controller
        self.__model: SettingsModel = model
        self.__controller_connected = False

        self.setupUi()
        if self.__controller is not None:
            self.set_controller(self.__controller)

    def set_controller(self, controller: SettingsWindowController):
        self.__controller = controller
        if not self.__controller_connected:
            self.__connect_controller_slots()
            self.__controller_connected = True

    def __connect_controller_slots(self):
        self.editDbConButton.clicked.connect(self.change_db_con_params_clicked)
        self.createProfileButton.clicked.connect(self.create_profile_clicked)
        self.editProfileButton.clicked.connect(self.__controller.start_profile_edit)
        self.saveProfileButton.clicked.connect(self.save_profile_clicked)
        self.deleteProfileButton.clicked.connect(self.__controller.delete_profile)
        self.cancelProfileEditButton.clicked.connect(self.cancel_profile_edit_clicked)
        self.setActiveProfileButton.clicked.connect(self.set_active_profile_clicked)
        self.profilesListWidget.itemSelectionChanged.connect(self.profile_selection_changed)
        self.profilesListWidget.itemDoubleClicked.connect(self.profile_double_clicked)
        self.rebuildGraphButton.clicked.connect(self.rebuild_graph_clicked)

    def __connect_model_slots(self):
        self.__model.profile_editing_state_changed.connect(self.__change_form_state)
        self.__model.active_profile_id_changed.connect(self.__active_profile_changed)
        self.__model.current_profile_id_changed.connect(self.__current_profile_changed)
        self.__model.profiles_changed.connect(self.__profiles_changed)

    def setupUi(self):
        self.setObjectName("SettingsDialog")
        self.resize(600, 400)

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")

        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")

        self.tabWidget = QtWidgets.QTabWidget(self)
        self.tabWidget.setObjectName("tabWidget")

        self.tabDb = QtWidgets.QWidget()
        self.tabDb.setObjectName("tabDb")

        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.tabDb)
        self.verticalLayout_5.setObjectName("verticalLayout_5")

        self.formLayout_2 = QtWidgets.QFormLayout()
        self.formLayout_2.setObjectName("formLayout_2")

        self.label_7 = QtWidgets.QLabel(self.tabDb)
        self.label_7.setObjectName("label_7")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_7)

        self.label_8 = QtWidgets.QLabel(self.tabDb)
        self.label_8.setObjectName("label_8")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_8)

        self.label_9 = QtWidgets.QLabel(self.tabDb)
        self.label_9.setObjectName("label_9")
        self.formLayout_2.setWidget(5, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_9)

        self.label_10 = QtWidgets.QLabel(self.tabDb)
        self.label_10.setObjectName("label_10")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_10)

        self.label_11 = QtWidgets.QLabel(self.tabDb)
        self.label_11.setObjectName("label_11")
        self.formLayout_2.setWidget(3, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_11)

        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")

        self.editDbConButton = QtWidgets.QPushButton(self.tabDb)
        self.editDbConButton.setObjectName("editDbConButton")
        self.horizontalLayout_4.addWidget(self.editDbConButton)
        self.formLayout_2.setLayout(6, QtWidgets.QFormLayout.ItemRole.FieldRole, self.horizontalLayout_4)

        self.dbHostnameEdit = QtWidgets.QLineEdit(self.tabDb)
        self.dbHostnameEdit.setEnabled(False)
        self.dbHostnameEdit.setMaxLength(200)
        self.dbHostnameEdit.setObjectName("dbHostnameEdit")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.dbHostnameEdit)

        self.dbPortEdit = QtWidgets.QLineEdit(self.tabDb)
        self.dbPortEdit.setEnabled(False)
        self.dbPortEdit.setMaxLength(6)
        self.dbPortEdit.setObjectName("dbPortEdit")
        self.formLayout_2.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.dbPortEdit)

        self.dbUsernameEdit = QtWidgets.QLineEdit(self.tabDb)
        self.dbUsernameEdit.setEnabled(False)
        self.dbUsernameEdit.setMaxLength(50)
        self.dbUsernameEdit.setObjectName("dbUsernameEdit")
        self.formLayout_2.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.dbUsernameEdit)

        self.dbPasswordEdit = QtWidgets.QLineEdit(self.tabDb)
        self.dbPasswordEdit.setEnabled(False)
        self.dbPasswordEdit.setMaxLength(50)
        self.dbPasswordEdit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.dbPasswordEdit.setObjectName("dbPasswordEdit")
        self.formLayout_2.setWidget(3, QtWidgets.QFormLayout.ItemRole.FieldRole, self.dbPasswordEdit)

        self.dbSchemaEdit = QtWidgets.QLineEdit(self.tabDb)
        self.dbSchemaEdit.setEnabled(False)
        self.dbSchemaEdit.setObjectName("dbSchemaEdit")
        self.formLayout_2.setWidget(5, QtWidgets.QFormLayout.ItemRole.FieldRole, self.dbSchemaEdit)

        self.label_13 = QtWidgets.QLabel(self.tabDb)
        self.label_13.setObjectName("label_13")
        self.formLayout_2.setWidget(4, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_13)

        self.dbDatabaseNameEdit = QtWidgets.QLineEdit(self.tabDb)
        self.dbDatabaseNameEdit.setEnabled(False)
        self.dbDatabaseNameEdit.setMaxLength(100)
        self.dbDatabaseNameEdit.setObjectName("dbDatabaseNameEdit")
        self.formLayout_2.setWidget(4, QtWidgets.QFormLayout.ItemRole.FieldRole, self.dbDatabaseNameEdit)
        self.verticalLayout_5.addLayout(self.formLayout_2)

        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_5.addItem(spacerItem)

        self.tabWidget.addTab(self.tabDb, "")

        self.tabProfiles = QtWidgets.QWidget()
        self.tabProfiles.setObjectName("tabProfiles")

        self.horizontalLayout = QtWidgets.QHBoxLayout(self.tabProfiles)
        self.horizontalLayout.setObjectName("horizontalLayout")

        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetDefaultConstraint)
        self.verticalLayout_4.setContentsMargins(-1, -1, 0, -1)
        self.verticalLayout_4.setObjectName("verticalLayout_4")

        self.profilesListWidget = QtWidgets.QListWidget(self.tabProfiles)
        self.profilesListWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.profilesListWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.profilesListWidget.setSelectionRectVisible(True)
        self.profilesListWidget.setItemAlignment(QtCore.Qt.AlignmentFlag.AlignLeading)
        self.profilesListWidget.setObjectName("profilesListWidget")
        self.verticalLayout_4.addWidget(self.profilesListWidget)

        self.gridLayout_3 = QtWidgets.QGridLayout()
        self.gridLayout_3.setContentsMargins(-1, -1, 0, 0)
        self.gridLayout_3.setObjectName("gridLayout_3")

        self.deleteProfileButton = QtWidgets.QPushButton(self.tabProfiles)
        self.deleteProfileButton.setEnabled(False)
        self.deleteProfileButton.setObjectName("deleteProfileButton")
        self.gridLayout_3.addWidget(self.deleteProfileButton, 1, 0, 1, 1)

        self.createProfileButton = QtWidgets.QPushButton(self.tabProfiles)
        self.createProfileButton.setObjectName("createProfileButton")
        self.gridLayout_3.addWidget(self.createProfileButton, 0, 0, 1, 1)

        self.setActiveProfileButton = QtWidgets.QPushButton(self.tabProfiles)
        self.setActiveProfileButton.setEnabled(False)
        self.setActiveProfileButton.setObjectName("setActiveProfileButton")
        self.gridLayout_3.addWidget(self.setActiveProfileButton, 3, 0, 1, 1)

        self.editProfileButton = QtWidgets.QPushButton(self.tabProfiles)
        self.editProfileButton.setEnabled(False)
        self.editProfileButton.setObjectName("editProfileButton")
        self.gridLayout_3.addWidget(self.editProfileButton, 2, 0, 1, 1)
        self.verticalLayout_4.addLayout(self.gridLayout_3)
        self.horizontalLayout.addLayout(self.verticalLayout_4)

        self.profilesFormLayout = QtWidgets.QGroupBox(self.tabProfiles)
        self.profilesFormLayout.setObjectName("profilesFormLayout")

        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.profilesFormLayout)
        self.verticalLayout_2.setContentsMargins(-1, 9, -1, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")

        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")

        self.label = QtWidgets.QLabel(self.profilesFormLayout)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label)

        self.label_2 = QtWidgets.QLabel(self.profilesFormLayout)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_2)

        self.label_3 = QtWidgets.QLabel(self.profilesFormLayout)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_3)

        self.label_4 = QtWidgets.QLabel(self.profilesFormLayout)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_4)

        self.label_5 = QtWidgets.QLabel(self.profilesFormLayout)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_5)

        self.profileNameEdit = QtWidgets.QLineEdit(self.profilesFormLayout)
        self.profileNameEdit.setEnabled(False)
        self.profileNameEdit.setMaxLength(50)
        self.profileNameEdit.setObjectName("profileNameEdit")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.profileNameEdit)

        self.profileHeightSpinBox = QtWidgets.QDoubleSpinBox(self.profilesFormLayout)
        self.profileHeightSpinBox.setEnabled(False)
        self.profileHeightSpinBox.setMaximum(999999.0)
        self.profileHeightSpinBox.setStepType(QtWidgets.QAbstractSpinBox.StepType.AdaptiveDecimalStepType)
        self.profileHeightSpinBox.setObjectName("profileHeightSpinBox")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.profileHeightSpinBox)

        self.profileWidthSpinBox = QtWidgets.QDoubleSpinBox(self.profilesFormLayout)
        self.profileWidthSpinBox.setEnabled(False)
        self.profileWidthSpinBox.setMaximum(999999.0)
        self.profileWidthSpinBox.setObjectName("profileWidthSpinBox")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.ItemRole.FieldRole, self.profileWidthSpinBox)

        self.profileWeightSpinBox = QtWidgets.QDoubleSpinBox(self.profilesFormLayout)
        self.profileWeightSpinBox.setEnabled(False)
        self.profileWeightSpinBox.setMaximum(999999.0)
        self.profileWeightSpinBox.setObjectName("profileWeightSpinBox")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.ItemRole.FieldRole, self.profileWeightSpinBox)

        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.formLayout.setItem(7, QtWidgets.QFormLayout.ItemRole.LabelRole, spacerItem1)

        self.vehicleTypeComboBox = QtWidgets.QComboBox(self.profilesFormLayout)
        self.vehicleTypeComboBox.setEnabled(False)
        for v_type in VehicleType:
            self.vehicleTypeComboBox.addItem(v_type.value, v_type)
        self.vehicleTypeComboBox.setObjectName("vehicleTypeComboBox")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.vehicleTypeComboBox)

        self.label_12 = QtWidgets.QLabel(self.profilesFormLayout)
        self.label_12.setObjectName("label_12")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_12)

        self.profileDepthSpinBox = QtWidgets.QDoubleSpinBox(self.profilesFormLayout)
        self.profileDepthSpinBox.setEnabled(False)
        self.profileDepthSpinBox.setMaximum(999999.0)
        self.profileDepthSpinBox.setObjectName("profileDepthSpinBox")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.ItemRole.FieldRole, self.profileDepthSpinBox)
        self.verticalLayout_2.addLayout(self.formLayout)

        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")

        self.saveProfileButton = QtWidgets.QPushButton(self.profilesFormLayout)
        self.saveProfileButton.setEnabled(False)
        self.saveProfileButton.setObjectName("saveProfileButton")
        self.horizontalLayout_2.addWidget(self.saveProfileButton)

        self.cancelProfileEditButton = QtWidgets.QPushButton(self.profilesFormLayout)
        self.cancelProfileEditButton.setEnabled(False)
        self.cancelProfileEditButton.setObjectName("cancelProfileEditButton")
        self.horizontalLayout_2.addWidget(self.cancelProfileEditButton)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout.addWidget(self.profilesFormLayout)
        self.tabWidget.addTab(self.tabProfiles, "")

        self.tabGraph = QtWidgets.QWidget()
        self.tabGraph.setObjectName("tabGraph")

        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.tabGraph)
        self.verticalLayout_3.setObjectName("verticalLayout_3")

        self.rebuildGraphButton = QtWidgets.QPushButton(self.tabGraph)
        self.rebuildGraphButton.setObjectName("rebuildGraphButton")
        self.verticalLayout_3.addWidget(self.rebuildGraphButton)

        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem2)
        self.tabWidget.addTab(self.tabGraph, "")
        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)

        self.retranslateUi()
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(self)
        self.__connect_model_slots()

        self.setTabOrder(self.tabWidget, self.dbHostnameEdit)
        self.setTabOrder(self.dbHostnameEdit, self.dbPortEdit)
        self.setTabOrder(self.dbPortEdit, self.dbUsernameEdit)
        self.setTabOrder(self.dbUsernameEdit, self.dbPasswordEdit)
        self.setTabOrder(self.dbPasswordEdit, self.dbDatabaseNameEdit)
        self.setTabOrder(self.dbDatabaseNameEdit, self.dbSchemaEdit)
        self.setTabOrder(self.dbSchemaEdit, self.profilesListWidget)
        self.setTabOrder(self.profilesListWidget, self.createProfileButton)
        self.setTabOrder(self.createProfileButton, self.deleteProfileButton)
        self.setTabOrder(self.deleteProfileButton, self.editProfileButton)
        self.setTabOrder(self.editProfileButton, self.setActiveProfileButton)
        self.setTabOrder(self.setActiveProfileButton, self.profileNameEdit)
        self.setTabOrder(self.profileNameEdit, self.vehicleTypeComboBox)
        self.setTabOrder(self.vehicleTypeComboBox, self.profileHeightSpinBox)
        self.setTabOrder(self.profileHeightSpinBox, self.profileWidthSpinBox)
        self.setTabOrder(self.profileWidthSpinBox, self.profileDepthSpinBox)
        self.setTabOrder(self.profileDepthSpinBox, self.profileWeightSpinBox)
        self.setTabOrder(self.profileWeightSpinBox, self.saveProfileButton)
        self.setTabOrder(self.saveProfileButton, self.cancelProfileEditButton)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("Dialog", "Настройки модуля"))
        self.label_7.setText(_translate("Dialog", "Хост:"))
        self.label_8.setText(_translate("Dialog", "Порт:"))
        self.label_9.setText(_translate("Dialog", "Схема:"))
        self.label_10.setText(_translate("Dialog", "Пользователь:"))
        self.label_11.setText(_translate("Dialog", "Пароль:"))
        self.editDbConButton.setText(_translate("Dialog", "Изменить"))
        self.dbHostnameEdit.setPlaceholderText(_translate("Dialog", "Например, localhost"))
        self.dbPortEdit.setPlaceholderText(_translate("Dialog", "Например, 5432"))
        self.dbUsernameEdit.setPlaceholderText(_translate("Dialog", "Например, postgres"))
        self.label_13.setText(_translate("Dialog", "База данных:"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabDb), _translate("Dialog", "База данных"))
        self.deleteProfileButton.setText(_translate("Dialog", "Удалить профиль"))
        self.createProfileButton.setText(_translate("Dialog", "Новый профиль"))
        self.setActiveProfileButton.setText(_translate("Dialog", "Выбрать в качестве активного профиля"))
        self.editProfileButton.setText(_translate("Dialog", "Изменить профиль"))
        self.profilesFormLayout.setTitle(_translate("Dialog", "Настройки профиля"))
        self.label.setText(_translate("Dialog", "Название:"))
        self.label_2.setText(_translate("Dialog", "Тип:"))
        self.label_3.setText(_translate("Dialog", "Высота:"))
        self.label_4.setText(_translate("Dialog", "Ширина:"))
        self.label_5.setText(_translate("Dialog", "Вес:"))
        self.profileNameEdit.setPlaceholderText(_translate("Dialog", "Профиль 1"))
        self.profileHeightSpinBox.setSuffix(_translate("Dialog", " м"))
        self.profileWidthSpinBox.setSuffix(_translate("Dialog", " м"))
        self.profileWeightSpinBox.setSuffix(_translate("Dialog", " т"))
        self.label_12.setText(_translate("Dialog", "Длина:"))
        self.profileDepthSpinBox.setSuffix(_translate("Dialog", " м"))
        self.saveProfileButton.setText(_translate("Dialog", "Сохранить"))
        self.cancelProfileEditButton.setText(_translate("Dialog", "Отмена"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabProfiles), _translate("Dialog", "Профили ТС"))
        self.rebuildGraphButton.setText(_translate("Dialog", "Перестроить граф дорог"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tabGraph), _translate("Dialog", "Граф дорог"))

    def set_tab_active(self, tab_index: int):
        self.tabWidget.setCurrentIndex(tab_index)

    def closeEvent(self, event, **kwargs):
        if self.__model.is_editing_enabled:
            close_question = self.__show_question_dialog(
                "Внимание",
                "Вы уверены, что хотите отменить несохранённые изменения и закрыть окно настроек?",
            )
            if close_question == QMessageBox.Yes:
                self.__controller.cancel_profile_edit()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


    def change_db_con_params_clicked(self):
        reconnect_question = self.__show_question_dialog(
            "Внимание",
            "Вы уверены, что хотите изменить настройки подключения к БД?",
        )
        if reconnect_question == QMessageBox.Yes:
            self.__controller.change_db_con_params()

    def rebuild_graph_clicked(self):
        rebuild_question = self.__show_question_dialog(
            "Внимание",
            "Вы уверены, что хотите перестроить граф?",
        )
        if rebuild_question == QMessageBox.Yes:
            self.__controller.rebuild_graph()

    def create_profile_clicked(self):
        self.clear_profile_form()
        self.profilesListWidget.clearSelection()
        self.__controller.start_profile_create()

    def save_profile_clicked(self):
        self.__controller.save_profile(*self.profile_form_data())

    def cancel_profile_edit_clicked(self):
        self.__controller.cancel_profile_edit()

    def profile_selection_changed(self):
        self.__controller.select_profile(self.selected_profile_id())

    def profile_double_clicked(self, item):
        self.__controller.set_active_profile(item.data(QtCore.Qt.ItemDataRole.UserRole))

    def set_active_profile_clicked(self):
        self.__controller.set_active_profile(self.selected_profile_id())

    @pyqtSlot(object)
    def __current_profile_changed(self, _profile_id=None):
        self.__refresh_profile_buttons()

    @pyqtSlot(object)
    def __active_profile_changed(self, _profile_id=None):
        self.__update_profiles_list(self.__model.profiles, self.__model.active_profile_id)

    @pyqtSlot(list)
    def __profiles_changed(self, profiles: list[VehicleProfile]):
        self.__update_profiles_list(profiles, self.__model.active_profile_id)

    @pyqtSlot(bool)
    def __change_form_state(self, enabled: bool):
        self.profileNameEdit.setEnabled(enabled)
        self.vehicleTypeComboBox.setEnabled(enabled)
        self.profileHeightSpinBox.setEnabled(enabled)
        self.profileWidthSpinBox.setEnabled(enabled)
        self.profileDepthSpinBox.setEnabled(enabled)
        self.profileWeightSpinBox.setEnabled(enabled)
        self.saveProfileButton.setEnabled(enabled)
        self.cancelProfileEditButton.setEnabled(enabled)
        self.__refresh_profile_buttons()

    def __update_profiles_list(self, profiles_list: list[VehicleProfile], active_id: int | None):
        current_profile_id = self.__model.current_profile_id
        self.profilesListWidget.blockSignals(True)
        self.profilesListWidget.clear()

        for profile in profiles_list:
            display_name = f"✓ {profile.name}" if profile.id == active_id else profile.name
            item = QListWidgetItem(display_name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, profile.id)
            self.profilesListWidget.addItem(item)
            if profile.id == current_profile_id:
                self.profilesListWidget.setCurrentItem(item)

        self.profilesListWidget.blockSignals(False)
        self.__refresh_profile_buttons()

    def __refresh_profile_buttons(self):
        has_selection = self.__model.current_profile_id is not None
        is_editing = self.__model.is_editing_enabled

        self.editProfileButton.setEnabled(has_selection and not is_editing)
        self.deleteProfileButton.setEnabled(has_selection and not is_editing)
        self.setActiveProfileButton.setEnabled(has_selection and not is_editing)
        self.createProfileButton.setEnabled(not is_editing)
        self.profilesListWidget.setEnabled(not is_editing)

    def selected_profile_id(self) -> int | None:
        item = self.profilesListWidget.currentItem()
        if item is None:
            return None
        return item.data(QtCore.Qt.ItemDataRole.UserRole)

    def profile_form_data(self):
        return (
            self.profileNameEdit.text().strip(),
            self.vehicleTypeComboBox.currentData(),
            self.profileHeightSpinBox.value(),
            self.profileWidthSpinBox.value(),
            self.profileDepthSpinBox.value(),
            self.profileWeightSpinBox.value(),
        )

    def set_profile_form(self, profile: VehicleProfile):
        self.profileNameEdit.setText(profile.name)
        index = self.vehicleTypeComboBox.findData(profile.type)
        if index < 0 and isinstance(profile.type, str):
            try:
                index = self.vehicleTypeComboBox.findData(VehicleType[profile.type])
            except KeyError:
                index = -1
        if index >= 0:
            self.vehicleTypeComboBox.setCurrentIndex(index)
        self.profileHeightSpinBox.setValue(profile.height_m)
        self.profileWidthSpinBox.setValue(profile.width_m)
        self.profileWeightSpinBox.setValue(profile.weight_t)
        self.profileDepthSpinBox.setValue(profile.depth_m)

    def clear_profile_form(self):
        self.profileNameEdit.clear()
        self.vehicleTypeComboBox.setCurrentIndex(0)
        self.profileHeightSpinBox.setValue(0)
        self.profileWidthSpinBox.setValue(0)
        self.profileWeightSpinBox.setValue(0)
        self.profileDepthSpinBox.setValue(0)

    def focus_profile_name(self):
        self.profileNameEdit.setFocus()

    def set_db_form(self, db):
        self.dbHostnameEdit.setText(db.host)
        self.dbPortEdit.setText(str(db.port))
        self.dbUsernameEdit.setText(db.username)
        self.dbPasswordEdit.setText(db.password)
        self.dbDatabaseNameEdit.setText(db.database)
        self.dbSchemaEdit.setText(db.schema)

    def show_warning(self, message: str):
        QMessageBox.warning(self, "", message, QMessageBox.Ok)

    def show_info(self, message: str):
        QMessageBox.information(self, "", message, QMessageBox.Ok)

    def show_error(self, message: str):
        QMessageBox.critical(self, "", message, QMessageBox.Ok)

    def confirm_delete_profile(self, profile_name: str, is_active: bool) -> bool:
        msg = "Вы пытаетесь удалить активный профиль.\n" if is_active else ""
        question = self.__show_question_dialog(
            "",
            f"{msg}Вы уверены, что хотите удалить профиль '{profile_name}'?",
        )
        return question == QMessageBox.Yes

    def __show_question_dialog(self, title: str, msg: str) -> QMessageBox:
        question = QMessageBox.question(
            self,
            title,
            msg,
            QMessageBox.Yes | QMessageBox.No
        )
        return question
