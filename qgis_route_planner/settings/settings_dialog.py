# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .settings_dialog_controller import SettingsDialogController
    from .settings_model import SettingsModel
    from .profile_dto import ProfileDto

from qgis.PyQt import QtCore, QtWidgets
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QObject, pyqtSlot

from qgis_route_planner.presentation import MessageBoxMixin, FormMode
from qgis_route_planner.vehicle.vehicle_type import VehicleType


class SettingsDialog(QtWidgets.QDialog, MessageBoxMixin):
    """ Окно настроек плагина """

    def __init__(
            self,
            model: SettingsModel,
            controller: SettingsDialogController,
            parent: QObject = None
    ):
        super().__init__(parent)

        self.__controller: SettingsDialogController = controller
        self.__model: SettingsModel = model

        self.__setupUi()

    def __connect(self):
        """ Подключение сигналов от контроллера и виджетов """
        # Сигналы от контроллера к view
        self.__controller.open_page_requested.connect(self.__open_dialog)
        self.__controller.show_error.connect(self._show_error)
        self.__controller.show_warning.connect(self._show_warning)
        self.__controller.show_info.connect(self._show_info)
        self.__controller.request_delete_confirmation.connect(self.__confirm_delete_profile)

        # Сигналы от модели к view
        self.__model.db_params_changed.connect(self.__on_db_params_changed)
        self.__model.profiles_changed.connect(self.__on_profiles_changed)
        self.__model.active_profile_id_changed.connect(self.__on_active_profile_changed)
        self.__model.selected_profile_id_changed.connect(self.__on_current_profile_changed)
        self.__model.editing_mode_changed.connect(self.__on_profile_editing_mode_changed)
        self.__model.selected_profile_data_changed.connect(self.__on_current_profile_data_changed)
        self.__model.weather_settings_changed.connect(self.__on_weather_settings_changed)
        self.__model.point_select_distance_changed.connect(self.__on_point_select_distance_changed)
        self.__model.basemap_settings_changed.connect(self.__on_basemap_settings_changed)

        # Сигналы от view к контроллеру
        self.__editDbConButton.clicked.connect(self.__on_change_db_clicked)

        self.__createProfileButton.clicked.connect(self.__on_create_profile_clicked)
        self.__editProfileButton.clicked.connect(self.__controller.start_profile_edit)
        self.__saveProfileButton.clicked.connect(self.__on_save_profile_clicked)
        self.__deleteProfileButton.clicked.connect(self.__controller.request_delete_profile)
        self.__cancelProfileEditButton.clicked.connect(self.__controller.cancel_profile_edit)
        self.__setActiveProfileButton.clicked.connect(self.__controller.set_active_profile)
        self.__profilesListWidget.itemSelectionChanged.connect(self.__on_profile_selection_changed)

        self.__rebuildGraphButton.clicked.connect(self.__on_rebuild_graph_clicked)
        self.__saveGraphSettingsButton.clicked.connect(self.__on_save_graph_settings_clicked)
        self.__checkServiceConButton.clicked.connect(self.__on_check_weather_clicked)
        self.__saveWeatherButton.clicked.connect(self.__on_save_weather_clicked)

    def __setupUi(self):
        self.setObjectName("SettingsDialog")
        self.resize(600, 400)
        self.setWindowIcon(QIcon(":/plugins/qgis_route_planner/plugin_icon"))

        self.__verticalLayout = QtWidgets.QVBoxLayout(self)
        self.__verticalLayout.setObjectName("verticalLayout")

        self.__gridLayout = QtWidgets.QGridLayout()
        self.__gridLayout.setObjectName("gridLayout")

        self.__tabWidget = QtWidgets.QTabWidget(self)
        self.__tabWidget.setObjectName("tabWidget")

        self.__tabDb = QtWidgets.QWidget()
        self.__tabDb.setObjectName("tabDb")

        self.__verticalLayout_5 = QtWidgets.QVBoxLayout(self.__tabDb)
        self.__verticalLayout_5.setObjectName("verticalLayout_5")

        self.__formLayout_2 = QtWidgets.QFormLayout()
        self.__formLayout_2.setObjectName("formLayout_2")

        self.__label_7 = QtWidgets.QLabel(self.__tabDb)
        self.__label_7.setObjectName("label_7")
        self.__formLayout_2.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.__label_7)

        self.__label_8 = QtWidgets.QLabel(self.__tabDb)
        self.__label_8.setObjectName("label_8")
        self.__formLayout_2.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.__label_8)

        self.__label_9 = QtWidgets.QLabel(self.__tabDb)
        self.__label_9.setObjectName("label_9")
        self.__formLayout_2.setWidget(5, QtWidgets.QFormLayout.ItemRole.LabelRole, self.__label_9)

        self.__label_10 = QtWidgets.QLabel(self.__tabDb)
        self.__label_10.setObjectName("label_10")
        self.__formLayout_2.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.__label_10)

        self.__label_11 = QtWidgets.QLabel(self.__tabDb)
        self.__label_11.setObjectName("label_11")
        self.__formLayout_2.setWidget(3, QtWidgets.QFormLayout.ItemRole.LabelRole, self.__label_11)

        self.__horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.__horizontalLayout_4.setContentsMargins(-1, 0, -1, -1)
        self.__horizontalLayout_4.setObjectName("horizontalLayout_4")

        self.__editDbConButton = QtWidgets.QPushButton(self.__tabDb)
        self.__editDbConButton.setObjectName("editDbConButton")
        self.__horizontalLayout_4.addWidget(self.__editDbConButton)
        self.__formLayout_2.setLayout(6, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__horizontalLayout_4)

        self.__dbHostnameEdit = QtWidgets.QLineEdit(self.__tabDb)
        self.__dbHostnameEdit.setEnabled(False)
        self.__dbHostnameEdit.setMaxLength(200)
        self.__dbHostnameEdit.setObjectName("dbHostnameEdit")
        self.__formLayout_2.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__dbHostnameEdit)

        self.__dbPortEdit = QtWidgets.QLineEdit(self.__tabDb)
        self.__dbPortEdit.setEnabled(False)
        self.__dbPortEdit.setMaxLength(6)
        self.__dbPortEdit.setObjectName("dbPortEdit")
        self.__formLayout_2.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__dbPortEdit)

        self.__dbUsernameEdit = QtWidgets.QLineEdit(self.__tabDb)
        self.__dbUsernameEdit.setEnabled(False)
        self.__dbUsernameEdit.setMaxLength(50)
        self.__dbUsernameEdit.setObjectName("dbUsernameEdit")
        self.__formLayout_2.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__dbUsernameEdit)

        self.__dbPasswordEdit = QtWidgets.QLineEdit(self.__tabDb)
        self.__dbPasswordEdit.setEnabled(False)
        self.__dbPasswordEdit.setMaxLength(50)
        self.__dbPasswordEdit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.__dbPasswordEdit.setObjectName("dbPasswordEdit")
        self.__formLayout_2.setWidget(3, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__dbPasswordEdit)

        self.__dbSchemaEdit = QtWidgets.QLineEdit(self.__tabDb)
        self.__dbSchemaEdit.setEnabled(False)
        self.__dbSchemaEdit.setObjectName("dbSchemaEdit")
        self.__formLayout_2.setWidget(5, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__dbSchemaEdit)

        self.__label_13 = QtWidgets.QLabel(self.__tabDb)
        self.__label_13.setObjectName("label_13")
        self.__formLayout_2.setWidget(4, QtWidgets.QFormLayout.ItemRole.LabelRole, self.__label_13)

        self.__dbDatabaseNameEdit = QtWidgets.QLineEdit(self.__tabDb)
        self.__dbDatabaseNameEdit.setEnabled(False)
        self.__dbDatabaseNameEdit.setMaxLength(100)
        self.__dbDatabaseNameEdit.setObjectName("dbDatabaseNameEdit")
        self.__formLayout_2.setWidget(4, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__dbDatabaseNameEdit)
        self.__verticalLayout_5.addLayout(self.__formLayout_2)

        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.__verticalLayout_5.addItem(spacerItem)

        self.__tabWidget.addTab(self.__tabDb, "")

        self.__tabProfiles = QtWidgets.QWidget()
        self.__tabProfiles.setObjectName("tabProfiles")

        self.__horizontalLayout = QtWidgets.QHBoxLayout(self.__tabProfiles)
        self.__horizontalLayout.setObjectName("horizontalLayout")

        self.__verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.__verticalLayout_4.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetDefaultConstraint)
        self.__verticalLayout_4.setContentsMargins(-1, -1, 0, -1)
        self.__verticalLayout_4.setObjectName("verticalLayout_4")

        self.__profilesListWidget = QtWidgets.QListWidget(self.__tabProfiles)
        self.__profilesListWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.__profilesListWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.__profilesListWidget.setSelectionRectVisible(True)
        self.__profilesListWidget.setItemAlignment(QtCore.Qt.AlignmentFlag.AlignLeading)
        self.__profilesListWidget.setObjectName("profilesListWidget")
        self.__verticalLayout_4.addWidget(self.__profilesListWidget)

        self.__gridLayout_3 = QtWidgets.QGridLayout()
        self.__gridLayout_3.setContentsMargins(-1, -1, 0, 0)
        self.__gridLayout_3.setObjectName("gridLayout_3")

        self.__deleteProfileButton = QtWidgets.QPushButton(self.__tabProfiles)
        self.__deleteProfileButton.setEnabled(False)
        self.__deleteProfileButton.setObjectName("deleteProfileButton")
        self.__gridLayout_3.addWidget(self.__deleteProfileButton, 1, 0, 1, 1)

        self.__createProfileButton = QtWidgets.QPushButton(self.__tabProfiles)
        self.__createProfileButton.setObjectName("createProfileButton")
        self.__gridLayout_3.addWidget(self.__createProfileButton, 0, 0, 1, 1)

        self.__setActiveProfileButton = QtWidgets.QPushButton(self.__tabProfiles)
        self.__setActiveProfileButton.setEnabled(False)
        self.__setActiveProfileButton.setObjectName("setActiveProfileButton")
        self.__gridLayout_3.addWidget(self.__setActiveProfileButton, 3, 0, 1, 1)

        self.__editProfileButton = QtWidgets.QPushButton(self.__tabProfiles)
        self.__editProfileButton.setEnabled(False)
        self.__editProfileButton.setObjectName("editProfileButton")
        self.__gridLayout_3.addWidget(self.__editProfileButton, 2, 0, 1, 1)
        self.__verticalLayout_4.addLayout(self.__gridLayout_3)
        self.__horizontalLayout.addLayout(self.__verticalLayout_4)

        self.__profilesFormLayout = QtWidgets.QGroupBox(self.__tabProfiles)
        self.__profilesFormLayout.setObjectName("profilesFormLayout")

        self.__verticalLayout_2 = QtWidgets.QVBoxLayout(self.__profilesFormLayout)
        self.__verticalLayout_2.setContentsMargins(-1, 9, -1, 0)
        self.__verticalLayout_2.setObjectName("verticalLayout_2")

        self.__formLayout = QtWidgets.QFormLayout()
        self.__formLayout.setObjectName("formLayout")

        self.__label = QtWidgets.QLabel(self.__profilesFormLayout)
        self.__label.setObjectName("label")
        self.__formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.__label)

        self.__label_2 = QtWidgets.QLabel(self.__profilesFormLayout)
        self.__label_2.setObjectName("label_2")
        self.__formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.__label_2)

        self.__label_3 = QtWidgets.QLabel(self.__profilesFormLayout)
        self.__label_3.setObjectName("label_3")
        self.__formLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.__label_3)

        self.__label_4 = QtWidgets.QLabel(self.__profilesFormLayout)
        self.__label_4.setObjectName("label_4")
        self.__formLayout.setWidget(3, QtWidgets.QFormLayout.ItemRole.LabelRole, self.__label_4)

        self.__label_5 = QtWidgets.QLabel(self.__profilesFormLayout)
        self.__label_5.setObjectName("label_5")
        self.__formLayout.setWidget(5, QtWidgets.QFormLayout.ItemRole.LabelRole, self.__label_5)

        self.__profileNameEdit = QtWidgets.QLineEdit(self.__profilesFormLayout)
        self.__profileNameEdit.setEnabled(False)
        self.__profileNameEdit.setMaxLength(50)
        self.__profileNameEdit.setObjectName("profileNameEdit")
        self.__formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__profileNameEdit)

        self.__profileHeightSpinBox = QtWidgets.QDoubleSpinBox(self.__profilesFormLayout)
        self.__profileHeightSpinBox.setEnabled(False)
        self.__profileHeightSpinBox.setMinimum(0.01)
        self.__profileHeightSpinBox.setMaximum(999999.0)
        self.__profileHeightSpinBox.setStepType(QtWidgets.QAbstractSpinBox.StepType.AdaptiveDecimalStepType)
        self.__profileHeightSpinBox.setObjectName("profileHeightSpinBox")
        self.__formLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__profileHeightSpinBox)

        self.__profileWidthSpinBox = QtWidgets.QDoubleSpinBox(self.__profilesFormLayout)
        self.__profileWidthSpinBox.setEnabled(False)
        self.__profileWidthSpinBox.setMinimum(0.01)
        self.__profileWidthSpinBox.setMaximum(999999.0)
        self.__profileWidthSpinBox.setObjectName("profileWidthSpinBox")
        self.__formLayout.setWidget(3, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__profileWidthSpinBox)

        self.__profileWeightSpinBox = QtWidgets.QDoubleSpinBox(self.__profilesFormLayout)
        self.__profileWeightSpinBox.setEnabled(False)
        self.__profileWeightSpinBox.setMinimum(0.01)
        self.__profileWeightSpinBox.setMaximum(999999.0)
        self.__profileWeightSpinBox.setObjectName("profileWeightSpinBox")
        self.__formLayout.setWidget(5, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__profileWeightSpinBox)

        __spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.__formLayout.setItem(7, QtWidgets.QFormLayout.ItemRole.LabelRole, __spacerItem1)

        self.__vehicleTypeComboBox = QtWidgets.QComboBox(self.__profilesFormLayout)
        self.__vehicleTypeComboBox.setEnabled(False)
        for v_type in VehicleType:
            self.__vehicleTypeComboBox.addItem(v_type.value, v_type)
        self.__vehicleTypeComboBox.setObjectName("vehicleTypeComboBox")
        self.__formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__vehicleTypeComboBox)

        self.__label_12 = QtWidgets.QLabel(self.__profilesFormLayout)
        self.__label_12.setObjectName("label_12")
        self.__formLayout.setWidget(4, QtWidgets.QFormLayout.ItemRole.LabelRole, self.__label_12)

        self.__profileDepthSpinBox = QtWidgets.QDoubleSpinBox(self.__profilesFormLayout)
        self.__profileDepthSpinBox.setEnabled(False)
        self.__profileDepthSpinBox.setMinimum(0.01)
        self.__profileDepthSpinBox.setMaximum(999999.0)
        self.__profileDepthSpinBox.setObjectName("profileDepthSpinBox")
        self.__formLayout.setWidget(4, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__profileDepthSpinBox)
        self.__verticalLayout_2.addLayout(self.__formLayout)

        self.__horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.__horizontalLayout_2.setObjectName("horizontalLayout_2")

        self.__saveProfileButton = QtWidgets.QPushButton(self.__profilesFormLayout)
        self.__saveProfileButton.setEnabled(False)
        self.__saveProfileButton.setObjectName("saveProfileButton")
        self.__horizontalLayout_2.addWidget(self.__saveProfileButton)

        self.__cancelProfileEditButton = QtWidgets.QPushButton(self.__profilesFormLayout)
        self.__cancelProfileEditButton.setEnabled(False)
        self.__cancelProfileEditButton.setObjectName("cancelProfileEditButton")
        self.__horizontalLayout_2.addWidget(self.__cancelProfileEditButton)
        self.__verticalLayout_2.addLayout(self.__horizontalLayout_2)
        self.__horizontalLayout.addWidget(self.__profilesFormLayout)
        self.__tabWidget.addTab(self.__tabProfiles, "")

        self.__tabGraph = QtWidgets.QWidget()
        self.__tabGraph.setObjectName("tabGraph")

        self.__verticalLayout_3 = QtWidgets.QVBoxLayout(self.__tabGraph)
        self.__verticalLayout_3.setObjectName("verticalLayout_3")

        self.__rebuildGraphButton = QtWidgets.QPushButton(self.__tabGraph)
        self.__rebuildGraphButton.setObjectName("rebuildGraphButton")
        self.__verticalLayout_3.addWidget(self.__rebuildGraphButton)

        __spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.__verticalLayout_3.addItem(__spacerItem2)

        self.__graphSettingsLayout = QtWidgets.QFormLayout()
        self.__graphSettingsLayout.setObjectName("graphSettingsLayout")

        self.__distanceLabel = QtWidgets.QLabel()
        self.__distanceLabel.setObjectName("distanceLabel")
        self.__graphSettingsLayout.setWidget(4, QtWidgets.QFormLayout.ItemRole.LabelRole, self.__distanceLabel)

        self.__distanceEdit = QtWidgets.QDoubleSpinBox()
        self.__distanceEdit.setObjectName("distanceEdit")
        self.__distanceEdit.setMaximum(1000.0)
        self.__distanceEdit.setMinimum(0.01)
        self.__distanceEdit.setSuffix(" м")
        self.__graphSettingsLayout.setWidget(4, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__distanceEdit)

        self.__basemapEnabledCheckBox = QtWidgets.QCheckBox()
        self.__basemapEnabledCheckBox.setObjectName("basemapEnabledCheckBox")
        self.__graphSettingsLayout.setWidget(5, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__basemapEnabledCheckBox)

        self.__basemapUrlLabel = QtWidgets.QLabel()
        self.__basemapUrlLabel.setObjectName("basemapUrlLabel")
        self.__graphSettingsLayout.setWidget(6, QtWidgets.QFormLayout.ItemRole.LabelRole, self.__basemapUrlLabel)

        self.__basemapUrlEdit = QtWidgets.QLineEdit()
        self.__basemapUrlEdit.setObjectName("basemapUrlEdit")
        self.__basemapUrlEdit.setClearButtonEnabled(True)
        self.__graphSettingsLayout.setWidget(6, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__basemapUrlEdit)

        self.__saveGraphSettingsButton = QtWidgets.QPushButton()
        self.__saveGraphSettingsButton.setObjectName("saveGraphSettingsButton")
        self.__graphSettingsLayout.setWidget(7, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__saveGraphSettingsButton)

        self.__verticalLayout_3.addLayout(self.__graphSettingsLayout)

        __spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.__verticalLayout_3.addItem(__spacerItem3)

        self.__tabWidget.addTab(self.__tabGraph, "")

        self.__tabWeather = QtWidgets.QWidget()
        self.__tabWeather.setObjectName("tabWeather")

        self.__tabWeatherLayout = QtWidgets.QFormLayout(self.__tabWeather)

        self.__urlLabel = QtWidgets.QLabel(self.__tabWeather)
        self.__urlLabel.setObjectName("urlLabel")
        self.__tabWeatherLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.__urlLabel)

        self.__urlLineEdit = QtWidgets.QLineEdit(self.__tabWeather)
        self.__urlLineEdit.setObjectName("urlLineEdit")
        self.__urlLineEdit.setEnabled(False)
        self.__tabWeatherLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__urlLineEdit)

        self.__keyLabel = QtWidgets.QLabel(self.__tabWeather)
        self.__keyLabel.setObjectName("keyLabel")
        self.__tabWeatherLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.__keyLabel)

        self.__keyLineEdit = QtWidgets.QLineEdit(self.__tabWeather)
        self.__keyLineEdit.setObjectName("keyLineEdit")
        self.__keyLineEdit.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.__tabWeatherLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__keyLineEdit)

        self.__fallbackSeasonLabel = QtWidgets.QLabel(self.__tabWeather)
        self.__fallbackSeasonLabel.setObjectName("fallbackSeasonLabel")
        self.__tabWeatherLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.__fallbackSeasonLabel)

        self.__fallbackSeasonComboBox = QtWidgets.QComboBox(self.__tabWeather)
        self.__fallbackSeasonComboBox.setObjectName("fallbackSeasonComboBox")
        self.__fallbackSeasonComboBox.addItem("", "summer")
        self.__fallbackSeasonComboBox.addItem("", "winter")
        self.__tabWeatherLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__fallbackSeasonComboBox)

        self.__weatherButtonsLayout = QtWidgets.QHBoxLayout()
        self.__weatherButtonsLayout.setObjectName("weatherButtonsLayout")

        self.__checkServiceConButton = QtWidgets.QPushButton(self.__tabWeather)
        self.__checkServiceConButton.setObjectName("checkServiceConButton")
        self.__weatherButtonsLayout.addWidget(self.__checkServiceConButton)

        self.__saveWeatherButton = QtWidgets.QPushButton(self.__tabWeather)
        self.__saveWeatherButton.setObjectName("saveWeatherButton")
        self.__weatherButtonsLayout.addWidget(self.__saveWeatherButton)

        self.__tabWeatherLayout.setLayout(4, QtWidgets.QFormLayout.ItemRole.FieldRole, self.__weatherButtonsLayout)
        self.__tabWidget.addTab(self.__tabWeather, "")

        self.__gridLayout.addWidget(self.__tabWidget, 0, 0, 1, 1)
        self.__verticalLayout.addLayout(self.__gridLayout)

        self.__retranslateUi()
        self.__tabWidget.setCurrentIndex(0)
        self.__connect()

        self.setTabOrder(self.__tabWidget, self.__dbHostnameEdit)
        self.setTabOrder(self.__dbHostnameEdit, self.__dbPortEdit)
        self.setTabOrder(self.__dbPortEdit, self.__dbUsernameEdit)
        self.setTabOrder(self.__dbUsernameEdit, self.__dbPasswordEdit)
        self.setTabOrder(self.__dbPasswordEdit, self.__dbDatabaseNameEdit)
        self.setTabOrder(self.__dbDatabaseNameEdit, self.__dbSchemaEdit)
        self.setTabOrder(self.__dbSchemaEdit, self.__profilesListWidget)
        self.setTabOrder(self.__profilesListWidget, self.__createProfileButton)
        self.setTabOrder(self.__createProfileButton, self.__deleteProfileButton)
        self.setTabOrder(self.__deleteProfileButton, self.__editProfileButton)
        self.setTabOrder(self.__editProfileButton, self.__setActiveProfileButton)
        self.setTabOrder(self.__setActiveProfileButton, self.__profileNameEdit)
        self.setTabOrder(self.__profileNameEdit, self.__vehicleTypeComboBox)
        self.setTabOrder(self.__vehicleTypeComboBox, self.__profileHeightSpinBox)
        self.setTabOrder(self.__profileHeightSpinBox, self.__profileWidthSpinBox)
        self.setTabOrder(self.__profileWidthSpinBox, self.__profileDepthSpinBox)
        self.setTabOrder(self.__profileDepthSpinBox, self.__profileWeightSpinBox)
        self.setTabOrder(self.__profileWeightSpinBox, self.__saveProfileButton)
        self.setTabOrder(self.__saveProfileButton, self.__cancelProfileEditButton)

    def __retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("Dialog", "Настройки модуля"))
        self.__label_7.setText(_translate("Dialog", "Хост:"))
        self.__label_8.setText(_translate("Dialog", "Порт:"))
        self.__label_9.setText(_translate("Dialog", "Схема:"))
        self.__label_10.setText(_translate("Dialog", "Пользователь:"))
        self.__label_11.setText(_translate("Dialog", "Пароль:"))
        self.__editDbConButton.setText(_translate("Dialog", "Изменить"))
        self.__dbHostnameEdit.setPlaceholderText(_translate("Dialog", "Например, localhost"))
        self.__dbPortEdit.setPlaceholderText(_translate("Dialog", "Например, 5432"))
        self.__dbUsernameEdit.setPlaceholderText(_translate("Dialog", "Например, postgres"))
        self.__label_13.setText(_translate("Dialog", "База данных:"))
        self.__tabWidget.setTabText(self.__tabWidget.indexOf(self.__tabDb), _translate("Dialog", "База данных"))
        self.__deleteProfileButton.setText(_translate("Dialog", "Удалить профиль"))
        self.__createProfileButton.setText(_translate("Dialog", "Новый профиль"))
        self.__setActiveProfileButton.setText(_translate("Dialog", "Выбрать в качестве активного профиля"))
        self.__editProfileButton.setText(_translate("Dialog", "Изменить профиль"))
        self.__profilesFormLayout.setTitle(_translate("Dialog", "Настройки профиля"))
        self.__label.setText(_translate("Dialog", "Название:"))
        self.__label_2.setText(_translate("Dialog", "Тип:"))
        self.__label_3.setText(_translate("Dialog", "Высота:"))
        self.__label_4.setText(_translate("Dialog", "Ширина:"))
        self.__label_5.setText(_translate("Dialog", "Вес:"))
        self.__profileNameEdit.setPlaceholderText(_translate("Dialog", "Профиль 1"))
        self.__profileHeightSpinBox.setSuffix(_translate("Dialog", " м"))
        self.__profileWidthSpinBox.setSuffix(_translate("Dialog", " м"))
        self.__profileWeightSpinBox.setSuffix(_translate("Dialog", " т"))
        self.__label_12.setText(_translate("Dialog", "Длина:"))
        self.__profileDepthSpinBox.setSuffix(_translate("Dialog", " м"))
        self.__saveProfileButton.setText(_translate("Dialog", "Сохранить"))
        self.__cancelProfileEditButton.setText(_translate("Dialog", "Отмена"))
        self.__tabWidget.setTabText(self.__tabWidget.indexOf(self.__tabProfiles), _translate("Dialog", "Профили ТС"))
        self.__rebuildGraphButton.setText(_translate("Dialog", "Перестроить граф дорог"))
        self.__tabWidget.setTabText(self.__tabWidget.indexOf(self.__tabGraph), _translate("Dialog", "Граф дорог"))
        self.__urlLabel.setText(_translate("Dialog", "URL сервиса:"))
        self.__urlLineEdit.setPlaceholderText(_translate("Dialog", "https://api.openweathermap.org/data/2.5/weather"))
        self.__keyLabel.setText(_translate("Dialog", "API-ключ:"))
        self.__fallbackSeasonLabel.setText(_translate("Dialog", "Сезон (оффлайн):"))
        self.__fallbackSeasonComboBox.setItemText(0, _translate("Dialog", "Летний"))
        self.__fallbackSeasonComboBox.setItemText(1, _translate("Dialog", "Зимний"))
        self.__checkServiceConButton.setText(_translate("Dialog", "Проверить подключение"))
        self.__saveWeatherButton.setText(_translate("Dialog", "Сохранить"))
        self.__tabWidget.setTabText(self.__tabWidget.indexOf(self.__tabWeather), _translate("Dialog", "Сервис погоды"))
        self.__saveGraphSettingsButton.setText(_translate("Dialog", "Сохранить"))
        self.__distanceLabel.setText(_translate("Dialog", "Расстояние захвата точки:"))
        self.__basemapEnabledCheckBox.setText(_translate("Dialog", "Подгружать подложку"))
        self.__basemapUrlLabel.setText(_translate("Dialog", "URL подложки:"))
        self.__basemapUrlEdit.setPlaceholderText(_translate("Dialog", "https://tile.openstreetmap.org/{z}/{x}/{y}.png"))

    # Слоты для сигналов от контроллера
    def __open_dialog(self, page_index: int):
        """ Открыть диалог на указанной вкладке """
        self.__tabWidget.setCurrentIndex(page_index)

        self.__on_db_params_changed(self.__model.db_params)
        self.__on_profiles_changed(self.__model.profiles)
        self.__on_weather_settings_changed(self.__model.weather_settings)
        self.__on_point_select_distance_changed(self.__model.point_select_distance)
        self.__on_basemap_settings_changed(self.__model.basemap_settings)

        self.show()

    def __confirm_delete_profile(self, profile_name: str):
        """ Показать диалог подтверждения удаления профиля """
        confirm_delete = self._show_question(
            f"Вы уверены, что хотите удалить профиль '{profile_name}'?",
            "Подтверждение удаления"
        )
        if confirm_delete:
            self.__controller.confirm_delete_profile()

    # Слоты для сигналов от модели
    @pyqtSlot(object)
    def __on_db_params_changed(self, db):
        """ Обновить отображение параметров БД """
        if db is None:
            return
        self.__dbHostnameEdit.setText(db.host)
        self.__dbPortEdit.setText(db.port)
        self.__dbUsernameEdit.setText(db.username)
        self.__dbPasswordEdit.setText(db.password)
        self.__dbDatabaseNameEdit.setText(db.database)
        self.__dbSchemaEdit.setText(db.schema)

    @pyqtSlot(list)
    def __on_profiles_changed(self, profiles: list[ProfileDto]):
        """ Обновить список профилей """
        self.__update_profiles_list(profiles, self.__model.active_profile_id)

    @pyqtSlot(object)
    def __on_active_profile_changed(self, profile_id: int):
        """ Обновить отображение активного профиля в списке """
        self.__update_profiles_list(self.__model.profiles, profile_id)

    def __select_item_by_profile_id(self, profile_id: int | None):
        """ Выделение элемента без перерисовки списка """
        if profile_id is None:
            self.__profilesListWidget.clearSelection()
            return

        for i in range(self.__profilesListWidget.count()):
            item = self.__profilesListWidget.item(i)
            if item.data(QtCore.Qt.ItemDataRole.UserRole) == profile_id:
                self.__profilesListWidget.setCurrentItem(item)
                break

    @pyqtSlot(object)
    def __on_current_profile_changed(self, profile_id: int):
        """ Выделить профиль в списке """
        self.__select_item_by_profile_id(profile_id)

    @pyqtSlot(FormMode)
    def __on_profile_editing_mode_changed(self, mode: FormMode):
        """ Обновить состояние формы редактирования """
        is_editing = mode == FormMode.EDIT or mode == FormMode.CREATE

        if mode == FormMode.CREATE:
            self.__clear_profile_form()

        self.__profileNameEdit.setEnabled(is_editing)
        self.__vehicleTypeComboBox.setEnabled(is_editing)
        self.__profileHeightSpinBox.setEnabled(is_editing)
        self.__profileWidthSpinBox.setEnabled(is_editing)
        self.__profileDepthSpinBox.setEnabled(is_editing)
        self.__profileWeightSpinBox.setEnabled(is_editing)
        self.__saveProfileButton.setEnabled(is_editing)
        self.__cancelProfileEditButton.setEnabled(is_editing)

        # Кнопки управления списком
        has_selection = self.__model.selected_profile_id is not None
        self.__editProfileButton.setEnabled(has_selection and not is_editing)
        self.__deleteProfileButton.setEnabled(has_selection and not is_editing)
        self.__setActiveProfileButton.setEnabled(has_selection and not is_editing)
        self.__createProfileButton.setEnabled(not is_editing)
        self.__profilesListWidget.setEnabled(not is_editing)

    @pyqtSlot(object)
    def __on_current_profile_data_changed(self, profile: ProfileDto):
        """ Обновить форму редактирования данными профиля """
        if profile is None:
            self.__clear_profile_form()
        else:
            self.__set_profile_form(profile)

    @pyqtSlot(dict)
    def __on_weather_settings_changed(self, settings: dict):
        """ Обновить форму погодных настроек """
        self.__urlLineEdit.setText(settings.get("api_url", ""))
        self.__keyLineEdit.setText(settings.get("api_key", ""))

        season = settings.get("fallback_season", "summer")
        season_index = self.__fallbackSeasonComboBox.findData(season)
        self.__fallbackSeasonComboBox.setCurrentIndex(season_index if season_index >= 0 else 0)

    @pyqtSlot(float)
    def __on_point_select_distance_changed(self, value: float):
        self.__distanceEdit.setValue(value)

    @pyqtSlot(dict)
    def __on_basemap_settings_changed(self, settings: dict):
        self.__basemapEnabledCheckBox.setChecked(bool(settings.get("basemap_enabled", False)))
        self.__basemapUrlEdit.setText(settings.get("basemap_url", ""))

    # Вспомогательные методы
    def __update_profiles_list(self, profiles_list: list[ProfileDto], active_id: int | None):
        """ Обновить список профилей в UI"""
        selected_profile_id = self.__model.selected_profile_id
        self.__profilesListWidget.blockSignals(True)
        self.__profilesListWidget.clear()

        for profile in profiles_list:
            display_name = f"✓ {profile.name}" if profile.id == active_id else profile.name
            item = QtWidgets.QListWidgetItem(display_name)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, profile.id)
            self.__profilesListWidget.addItem(item)

        self.__select_item_by_profile_id(self.__model.selected_profile_id)

        self.__profilesListWidget.blockSignals(False)

    def __set_profile_form(self, profile: ProfileDto):
        """ Заполнить форму данными профиля """
        self.__profileNameEdit.setText(profile.name)

        index = self.__vehicleTypeComboBox.findData(profile.type)
        self.__vehicleTypeComboBox.setCurrentIndex(index)

        self.__profileHeightSpinBox.setValue(profile.height)
        self.__profileWidthSpinBox.setValue(profile.width)
        self.__profileWeightSpinBox.setValue(profile.weight)
        self.__profileDepthSpinBox.setValue(profile.depth)

    def __clear_profile_form(self):
        """ Очистить форму профиля """
        self.__profileNameEdit.clear()
        self.__vehicleTypeComboBox.setCurrentIndex(0)
        self.__profileHeightSpinBox.setValue(0)
        self.__profileWidthSpinBox.setValue(0)
        self.__profileWeightSpinBox.setValue(0)
        self.__profileDepthSpinBox.setValue(0)

    # Слоты для событий от виджетов
    def __on_change_db_clicked(self):
        """ Обработчик нажатия на кнопку изменения БД """
        confirm_change = self._show_question(
            "Вы уверены, что хотите изменить настройки подключения к БД?",
        )
        if confirm_change:
            # Здесь должен быть вызов метода контроллера для изменения БД0-
            self.__controller.change_db_connection()

    def __on_rebuild_graph_clicked(self):
        """ Обработчик нажатия на кнопку перестроения графа """
        confirm_rebuild = self._show_question(
            "Вы уверены, что хотите перестроить граф?"
        )
        if confirm_rebuild:
            self.__controller.rebuild_graph()

    def __on_save_graph_settings_clicked(self):
        self.__controller.save_graph_settings(
            self.__distanceEdit.value(),
            self.__basemapEnabledCheckBox.isChecked(),
            self.__basemapUrlEdit.text(),
        )

    def __on_check_weather_clicked(self):
        """ Обработчик проверки подключения к погодному сервису """
        self.__controller.check_weather_connection(
            self.__urlLineEdit.text(),
            self.__keyLineEdit.text()
        )

    def __on_save_weather_clicked(self):
        """ Обработчик сохранения погодных настроек """
        self.__controller.save_weather_settings(
            self.__urlLineEdit.text(),
            self.__keyLineEdit.text(),
            self.__fallbackSeasonComboBox.currentData(),
        )

    def __on_save_profile_clicked(self):
        """ Обработчик сохранения профиля """
        self.__controller.save_profile(
            self.__profileNameEdit.text(),
            self.__vehicleTypeComboBox.currentData(),
            self.__profileHeightSpinBox.value(),
            self.__profileWidthSpinBox.value(),
            self.__profileDepthSpinBox.value(),
            self.__profileWeightSpinBox.value(),
        )

    def __on_create_profile_clicked(self):
        """ Обработчик создания нового профиля """
        self.__profilesListWidget.clearSelection()
        self.__clear_profile_form()
        self.__controller.start_profile_create()

    def __on_profile_selection_changed(self):
        """ Обработчик изменения выделения в списке профилей """
        profile_id = self.__get_selected_profile_id()
        self.__controller.select_profile(profile_id)

    def __get_selected_profile_id(self) -> int | None:
        """ Получить ID выбранного профиля"""
        item = self.__profilesListWidget.currentItem()
        if item is None:
            return None
        return item.data(QtCore.Qt.ItemDataRole.UserRole)

    def closeEvent(self, event):
        """ Обработчик закрытия окна """
        if self.__model.editing_mode == FormMode.EDIT or self.__model.editing_mode == FormMode.CREATE:
            close_question = self._show_question(
                "Вы уверены, что хотите отменить несохранённые изменения и закрыть окно настроек?"
            )
            if close_question:
                self.__controller.cancel_profile_edit()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
