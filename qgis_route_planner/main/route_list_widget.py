# -*- coding: utf-8 -*-
from qgis.PyQt import QtCore, QtGui, QtWidgets
from qgis.PyQt.QtCore import pyqtSignal
from qgis.PyQt.QtWidgets import QToolBox, QWidget

from qgis_route_planner.main.route_list_page import RouteListPage


class RouteListWidget(QToolBox):
    route_selected = pyqtSignal(int)
    route_save_requested = pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent)
        self.__pages: list[QWidget] = []
        self.__setupUi()

    def __setupUi(self):
        self.setObjectName("RouteListWidget")
        self.resize(400, 300)

        font = QtGui.QFont()
        font.setBold(True)
        font.setItalic(False)

        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")

        self.setFont(font)
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.setObjectName("routeListWidget")
        self.currentChanged.connect(self.route_selected.emit)

        self.retranslateUi()
        self.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("Form", "Виджет списка маршрутов"))

    def add_page(self, route_id: int, route: list, info: dict):
        route_page = RouteListPage(route_id, route, info, self)
        route_page.route_save_requested.connect(self.__open_file_fialog)
        self.__pages.append(route_page)
        self.addItem(route_page, f"Маршрут №{route_id + 1}")

    def save_route(self):
        pass

    def clear(self):
        while self.count() > 0:
            widget = self.widget(0)
            self.removeItem(0)
            if widget:
                widget.deleteLater()
        self.__pages.clear()

    def __open_file_fialog(self, route_id: int):
        self.route_save_requested.emit(route_id)