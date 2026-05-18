# -*- coding: utf-8 -*-

from qgis.PyQt import QtCore, QtWidgets

from ..views.widgets import MapWidget, RouteListWidget

class PluginMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi()

    def setupUi(self):
        self.setObjectName("self")
        self.resize(800, 600)

        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")

        self.gridLayout_3 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_3.setObjectName("gridLayout_3")

        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetMinimumSize)
        self.verticalLayout.setObjectName("verticalLayout")

        self.tabWidget = QtWidgets.QTabWidget(self.centralwidget)
        self.tabWidget.setSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Expanding)
        self.tabWidget.setEnabled(True)
        self.tabWidget.setElideMode(QtCore.Qt.TextElideMode.ElideNone)
        self.tabWidget.setTabBarAutoHide(False)
        self.tabWidget.setObjectName("tabWidget")

        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")

        self.gridLayout_2 = QtWidgets.QGridLayout(self.tab)
        self.gridLayout_2.setObjectName("gridLayout_2")

        self.points_list_widget = QtWidgets.QListWidget(self.tab)
        self.points_list_widget.setObjectName("points_list_widget")
        self.gridLayout_2.addWidget(self.points_list_widget, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")

        self.gridLayout = QtWidgets.QGridLayout(self.tab_2)
        self.gridLayout.setObjectName("gridLayout")

        self.route_list_widget = RouteListWidget(self.tab_2)
        self.gridLayout.addWidget(self.route_list_widget, 0, 0, 1, 1)

        self.tabWidget.addTab(self.tab_2, "")
        self.verticalLayout.addWidget(self.tabWidget)

        self.clear_list_button = QtWidgets.QPushButton(self.centralwidget)
        self.clear_list_button.setEnabled(False)
        self.clear_list_button.setObjectName("clear_list_button")

        self.verticalLayout.addWidget(self.clear_list_button)

        self.gridLayout_3.addLayout(self.verticalLayout, 0, 1, 1, 1)

        self.mapView = MapWidget()
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.mapView.sizePolicy().hasHeightForWidth())
        self.mapView.setSizePolicy(sizePolicy)
        self.mapView.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.mapView.setObjectName("mapView")
        self.gridLayout_3.addWidget(self.mapView, 0, 0, 1, 1)

        self.setCentralWidget(self.centralwidget)

        self.menubar = QtWidgets.QMenuBar(self)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 33))
        self.menubar.setObjectName("menubar")

        self.settings_menu = QtWidgets.QMenu(self.menubar)
        self.settings_menu.setObjectName("settings_menu")
        self.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

        self.db_action = QtWidgets.QAction(self)
        self.db_action.setObjectName("db_action")

        self.profiles_action = QtWidgets.QAction(self)
        self.profiles_action.setObjectName("profiles_action")

        self.graph_action = QtWidgets.QAction(self)
        self.graph_action.setObjectName("graph_action")

        self.settings_menu.addAction(self.db_action)
        self.settings_menu.addAction(self.profiles_action)
        self.settings_menu.addAction(self.graph_action)
        self.menubar.addAction(self.settings_menu.menuAction())

        self.about_menu = QtWidgets.QMenu(self.menubar)
        self.about_menu.setObjectName("about_menu")
        self.setMenuBar(self.menubar)

        self.about_action = QtWidgets.QAction(self)
        self.about_action.setObjectName("about_action")
        self.about_menu.addAction(self.about_action)
        self.menubar.addAction(self.about_menu.menuAction())

        self.retranslateUi()
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(self)

        self.mapView.show()

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "Поиск маршрутов"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Точки"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Маршруты"))
        self.clear_list_button.setText(_translate("MainWindow", "Построить новый маршрут"))
        self.settings_menu.setTitle(_translate("MainWindow", "Настройки"))
        self.about_menu.setTitle(_translate("MainWindow", "Справка"))
        self.about_action.setText(_translate("MainWindow", "О модуле"))
        self.profiles_action.setText(_translate("MainWindow", "Профили транспортных средств"))
        self.db_action.setText(_translate("MainWindow", "Подключение к базе данных"))
        self.graph_action.setText(_translate("MainWindow", "Настройки графа дорог"))

    def set_tab_active(self, tab_index: int):
        self.tabWidget.setCurrentIndex(tab_index)

    def clear_routes_list(self):
        """Очищает список маршрутов"""
        self.route_list_widget.clear()

    def clear_points_list(self):
        """Очищает список точек"""
        self.points_list_widget.clear()
