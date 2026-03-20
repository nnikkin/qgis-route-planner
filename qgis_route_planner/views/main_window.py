# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..controllers import MainWindowController
    from ..data.models import MainWindowModel

from qgis.PyQt import QtCore, QtWidgets
from qgis.PyQt.QtCore import pyqtSlot
from qgis.PyQt.QtWidgets import QAction, QMenu
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtCore import Qt

from qgis.core import (
    QgsGeometry, QgsPointXY, QgsWkbTypes, QgsVectorLayer,
    QgsPalLayerSettings, QgsVectorLayerSimpleLabeling
)
from qgis.gui import (
    QgsMapToolPan, QgsMapToolZoom, QgsRubberBand, QgsVertexMarker
)

from ..data.route import RoutePoint, PointType
from .widgets.map_widget import MapWidget
from .widgets.route_list_widget import RouteListWidget
from .message_box_mixin import MessageBoxMixin


class PluginMainWindow(QtWidgets.QMainWindow, MessageBoxMixin):
    """Главное окно плагина"""

    def __init__(self, model: MainWindowModel, controller: MainWindowController):
        super().__init__()
        self.__model: MainWindowModel = model
        self.__controller: MainWindowController = controller
        self.__restriction_dialog = None

        self.__point_markers: dict[int, QgsVertexMarker] = {}
        self.__route_bands: list[list[QgsRubberBand]] = []

        self.__restriction_markers: dict[int, QgsVertexMarker] = {}
        self.__restriction_band = None

        self.__restr_mode: bool = False

        self.setupUi()

    def setupUi(self):
        self.setObjectName("PluginMainWindow")
        self.resize(800, 600)

        self.central_widget = QtWidgets.QWidget(self)
        self.gridLayout_3 = QtWidgets.QGridLayout(self.central_widget)

        self.verticalLayout = QtWidgets.QVBoxLayout()

        self.tabWidget = QtWidgets.QTabWidget(self.central_widget)
        self.tabWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Expanding
        )

        # Вкладка "Точки"
        self.tab = QtWidgets.QWidget()
        self.gridLayout_2 = QtWidgets.QGridLayout(self.tab)
        self.points_list_widget = QtWidgets.QListWidget(self.tab)
        self.gridLayout_2.addWidget(self.points_list_widget, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab, "Точки")

        # Вкладка "Маршруты"
        self.tab_2 = QtWidgets.QWidget()
        self.gridLayout = QtWidgets.QGridLayout(self.tab_2)
        self.route_list_widget = RouteListWidget(self.tab_2)
        self.gridLayout.addWidget(self.route_list_widget, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab_2, "Маршруты")

        self.verticalLayout.addWidget(self.tabWidget)

        self.clear_list_button = QtWidgets.QPushButton("Построить новый маршрут", self.central_widget)
        self.clear_list_button.setEnabled(False)
        self.verticalLayout.addWidget(self.clear_list_button)

        self.gridLayout_3.addLayout(self.verticalLayout, 0, 1, 1, 1)

        # Карта
        self.mapView = MapWidget()
        self.mapView.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        self.gridLayout_3.addWidget(self.mapView, 0, 0, 1, 1)
        self.setCentralWidget(self.central_widget)

        # Меню
        self.menubar = QtWidgets.QMenuBar(self)
        self.settings_menu = QtWidgets.QMenu("Настройки", self.menubar)
        self.about_menu = QtWidgets.QMenu("Справка", self.menubar)

        self.db_action = QtWidgets.QAction("Подключение к базе данных", self)
        self.profiles_action = QtWidgets.QAction("Профили транспортных средств", self)
        self.graph_action = QtWidgets.QAction("Настройки графа дорог", self)
        self.about_action = QtWidgets.QAction("О модуле", self)

        self.settings_menu.addActions([self.db_action, self.profiles_action, self.graph_action])
        self.about_menu.addAction(self.about_action)
        self.menubar.addMenu(self.settings_menu)
        self.menubar.addMenu(self.about_menu)
        self.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)

        self.retranslateUi()
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(self)

        self.__setup_map_tools()
        self.__connect()

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

    def __setup_map_tools(self):
        self.__zoom_in_tool = QgsMapToolZoom(self.mapView, False)
        self.__zoom_out_tool = QgsMapToolZoom(self.mapView, True)
        self.__pan_tool = QgsMapToolPan(self.mapView)

        from ..views.widgets import SelectPointMapTool
        self.__select_route_point_tool = SelectPointMapTool(self.mapView)
        self.__select_restriction_point_tool = SelectPointMapTool(self.mapView)

    def __connect(self):
        self.__model.points_changed.connect(self.__on_points_changed)
        self.__model.routes_changed.connect(self.__on_routes_changed)
        self.__model.active_route_changed.connect(self.__on_active_route_changed)
        self.__model.status_message_changed.connect(self.__on_status_message_changed)
        self.__model.active_tab_changed.connect(self.tabWidget.setCurrentIndex)
        self.__model.clear_button_enabled_changed.connect(self.clear_list_button.setEnabled)

        self.__controller.layers_obtained.connect(self.__initialize_map)
        self.__controller.show_point_context_menu_requested.connect(self.__show_context_menu_for_point)
        self.__controller.routes_display_requested.connect(self.__display_routes)
        self.__controller.map_cleared.connect(self.__clear_map_visuals)
        self.__controller.point_marker_add_requested.connect(self.__add_point_marker)
        self.__controller.point_marker_remove_requested.connect(self.__remove_point_marker)
        self.__controller.point_marker_update_requested.connect(self.__update_point_marker_color)
        self.__controller.restriction_point_added.connect(self.__add_restriction_point_marker)
        self.__controller.restriction_band_added.connect(self.__display_restriction_band)
        self.__controller.restriction_band_cleared.connect(self.__clear_restriction_band)

        self.__controller.select_point_on_map_requested.connect(
            lambda: self.mapView.setMapTool(self.__select_restriction_point_tool)
        )

        self.__connect_ui_to_controller()

    def __connect_ui_to_controller(self):
        self.db_action.triggered.connect(
            lambda: self.__controller.open_settings_dialog(0)
        )
        self.profiles_action.triggered.connect(
            lambda: self.__controller.open_settings_dialog(1)
        )
        self.graph_action.triggered.connect(
            lambda: self.__controller.open_settings_dialog(2)
        )
        self.about_action.triggered.connect(self.__open_about_dialog)

        self.mapView.zoom_in_btn.clicked.connect(lambda: self.mapView.setMapTool(self.__zoom_in_tool))
        self.mapView.zoom_out_btn.clicked.connect(lambda: self.mapView.setMapTool(self.__zoom_out_tool))
        self.mapView.pan_btn.clicked.connect(lambda: self.mapView.setMapTool(self.__pan_tool))
        self.mapView.select_route_points_btn.clicked.connect(
            lambda: self.mapView.setMapTool(self.__select_route_point_tool)
        )
        self.mapView.open_restriction_dialog_btn.clicked.connect(
            self.__activate_restriction_mode
        )

        self.__select_route_point_tool.pointClicked.connect(self.__controller.on_map_point_selected)
        self.__select_restriction_point_tool.pointClicked.connect(self.__controller.on_map_point_selected)

        self.clear_list_button.clicked.connect(self.__controller.on_clear_everything)
        self.route_list_widget.route_selected.connect(self.__controller.on_route_selected)
        self.route_list_widget.route_save_requested.connect(self.__controller.on_save_route)

    @pyqtSlot(list)
    def __on_points_changed(self, points: list[RoutePoint]):
        self.points_list_widget.clear()
        for route_point in points:
            if route_point.point_type == PointType.START:
                prefix = "НАЧАЛО"
            elif route_point.point_type == PointType.END:
                prefix = "КОНЕЦ"
            else:
                prefix = f"Точка {route_point.order}"

            item = QtWidgets.QListWidgetItem(
                f"{prefix}: ({route_point.qgs_point_xy.x():.6f}, {route_point.qgs_point_xy.y():.6f})"
            )
            item.setData(Qt.ItemDataRole.UserRole, route_point.id)
            self.points_list_widget.addItem(item)

    @pyqtSlot(list)
    def __on_routes_changed(self, routes: list):
        self.route_list_widget.clear()
        for i, route in enumerate(routes):
            info = self.__get_route_info(route)
            self.route_list_widget.add_page(i, route, info)

    @pyqtSlot(int)
    def __on_active_route_changed(self, index: int):
        self.__highlight_routes(index)

    @pyqtSlot(str)
    def __on_status_message_changed(self, message: str):
        """Обрабатывает статусные сообщения и коды ошибок от контроллера"""
        error_messages = {
            "error:snap": (
                "Не удалось привязать точку к дорожной сети.\n"
                "Пожалуйста, выберите точку ближе к дороге."
            ),
            "error:no_node": (
                "Не удалось найти ближайший узел дорожной сети.\n"
                "Пожалуйста, выберите точку ближе к дороге."
            ),
            "error:no_routes": "Маршруты между выбранными точками не найдены.",
        }

        if message == "error:no_profile":
            q = self._show_question(
                "Сначала нужно создать профиль транспортного средства."
                "\nВы хотите перейти в настройки модуля?"
            )
            if q:
                self.__controller.open_settings_dialog(1)
        elif message in error_messages and error_messages[message]:
            self._show_warning(error_messages[message])
        else:
            self.statusBar().showMessage(message)

    @pyqtSlot(object, int)
    def __show_context_menu_for_point(self, point: QgsPointXY, node_id: int):
        """Показать контекстное меню точки"""
        menu = QMenu(self.mapView)

        if self.__restr_mode:
            action = QAction("Установить ограничение", menu)
            action.triggered.connect(
                lambda p=point, nid=node_id:
                self.__controller.on_add_restriction_point(p, nid)
            )
            menu.addAction(action)

            action = QAction("Отмена", menu)
            action.triggered.connect(
                self.__cancel_restriction_selection
            )
            menu.addAction(action)

        else:
            points = self.__model.points
            has_start = any(p.point_type == PointType.START for p in points)
            has_end = any(p.point_type == PointType.END for p in points)

            actions = [
                ("Установить как начальную точку", PointType.START, not has_start),
                ("Установить как промежуточную точку", PointType.WAYPOINT, has_start),
                ("Установить как конечную точку", PointType.END, has_start and not has_end),
            ]
            for title, point_type, enabled in actions:
                action = QAction(title, menu)
                action.triggered.connect(
                    lambda checked=False, pt=point_type, p=point, nid=node_id:
                        self.__controller.on_add_route_point(p, pt, nid)
                )
                action.setEnabled(enabled)
                menu.addAction(action)

        menu.exec_(QCursor.pos())

    @pyqtSlot(object)
    def __add_point_marker(self, route_point: RoutePoint):
        """Добавить маркер на карту"""
        marker = QgsVertexMarker(self.mapView)
        marker.setCenter(route_point.qgs_point_xy)
        marker.setIconType(QgsVertexMarker.IconType.ICON_CIRCLE)
        marker.setIconSize(10)
        marker.setPenWidth(
            3 if route_point.point_type in {PointType.START, PointType.END} else 2
        )
        self.__set_marker_color(marker, route_point.point_type)
        marker.show()
        self.__point_markers[route_point.id] = marker

    @pyqtSlot(int)
    def __remove_point_marker(self, point_id: int):
        """Убрать маркер с карты"""
        marker = self.__point_markers.pop(point_id, None)
        if marker:
            self.mapView.scene().removeItem(marker)

    @pyqtSlot(int)
    def __update_point_marker_color(self, point_id: int):
        """Изменить цвет маркера"""
        marker = self.__point_markers.get(point_id)
        if not marker:
            return
        point = next((p for p in self.__model.points if p.id == point_id), None)
        if point:
            self.__set_marker_color(marker, point.point_type)

    @pyqtSlot(list)
    def __display_routes(self, routes: list):
        """Метод для отображения маршрутов на карте"""
        self.__clear_route_bands()
        if not routes:
            return

        extent = None
        for route in routes:
            band_list = []
            for edge in route:
                geom = QgsGeometry.fromWkt(edge["geom"])
                if geom.isNull():
                    continue
                band = QgsRubberBand(self.mapView, QgsWkbTypes.LineGeometry)
                band.setColor(Qt.gray)
                band.setWidth(3)
                band.setToGeometry(geom, None)
                band_list.append(band)

                bb = geom.boundingBox()
                extent = bb if extent is None else (extent.combineExtentWith(bb) or extent)

            self.__route_bands.append(band_list)

        if extent:
            self.mapView.setExtent(extent)

        self.__highlight_routes(0)
        self.mapView.refresh()

    def __highlight_routes(self, active_index: int):
        """Подсветка маршрута"""
        for i, band_list in enumerate(self.__route_bands):
            is_active = (i == active_index)
            for band in band_list:
                band.setColor(Qt.blue if is_active else Qt.darkGray)
                band.setWidth(5 if is_active else 3)
                band.setZValue(1 if is_active else 0)
        self.mapView.refresh()

    @pyqtSlot()
    def __clear_map_visuals(self):
        for marker in self.__point_markers.values():
            self.mapView.scene().removeItem(marker)
        self.__point_markers.clear()
        self.__clear_route_bands()
        self.points_list_widget.clear()
        self.route_list_widget.clear()

    def __clear_route_bands(self):
        for band_list in self.__route_bands:
            for band in band_list:
                self.mapView.scene().removeItem(band)
        self.__route_bands = []

    @pyqtSlot(list)
    def __initialize_map(self, layers: list[QgsVectorLayer]):
        """Принимает слои от контроллера и устанавливает их на карту"""
        self.mapView.set_layers(layers)
        for layer in layers:
            if 'graph_edges' in layer.name() and layer.fields().indexOf('name') >= 0:
                settings = QgsPalLayerSettings()
                settings.fieldName = 'name'
                settings.enabled = True
                layer.setLabelsEnabled(True)
                layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
                layer.triggerRepaint()

    def __set_marker_color(self, marker: QgsVertexMarker, point_type: PointType):
        """Установить цвет маркера"""
        colors = {
            PointType.START: Qt.green,
            PointType.END: Qt.magenta,
            PointType.WAYPOINT: Qt.black,
            PointType.RESTRICTION: Qt.red
        }
        marker.setColor(colors.get(point_type, Qt.black))

    def __get_route_info(self, route: list[dict]) -> dict:
        """Получить информацию по маршруту"""
        if not route:
            return {'distance_km': 0, 'time_minutes': 0, 'segments': 0}
        return {
            'distance_km': sum(e['length_m'] for e in route) / 1000,
            'time_minutes': sum(e['cost'] for e in route) / 60,
            'segments': len(route),
        }

    def __activate_restriction_mode(self):
        """Активировать режим выбора точек для ограничений"""
        self.__restr_mode = True
        self.__controller.open_restriction_dialog()

    def __cancel_restriction_selection(self):
        self.__restr_mode = False
        self.mapView.setMapTool(None)
        self.__controller.cancel_add_restriction_point()

    def __on_restriction_point_clicked(self, point: QgsPointXY):
        """Обработчик клика для выбора точки ограничения"""
        self.mapView.setMapTool(self.__pan_tool)
        self.statusBar().clearMessage()

        # Привязываем точку к дороге
        snapped = self.__controller.snap_point(point)
        if not snapped:
            self._show_warning("Точка не привязана к дорожной сети!")
            return

        snapped_point, node_id = snapped

        if self.__restriction_dialog:
            self.__restriction_dialog.add_node_to_list(node_id, snapped_point.x(), snapped_point.y())
            self.__restriction_dialog.show()

    def __add_restriction_point_marker(self, node_id: int, x: float, y: float):
        """Добавить маркер точки ограничения на карту"""
        marker = QgsVertexMarker(self.mapView)
        marker.setCenter(QgsPointXY(x, y))
        marker.setIconType(QgsVertexMarker.IconType.ICON_CROSS)
        marker.setColor(Qt.red)
        marker.setIconSize(12)
        marker.setPenWidth(2)
        marker.show()

        if not self.__restriction_markers:
            self.__restriction_markers = {}
        self.__restriction_markers[node_id] = marker

    def __display_restriction_band(self, route: list[dict]):
        """Отобразить ограничения линией"""
        self.__clear_restriction_band()

        band = QgsRubberBand(self.mapView, QgsWkbTypes.LineGeometry)
        band.setColor(Qt.red)
        band.setWidth(4)

        for edge in route:
            geom = QgsGeometry.fromWkt(edge["geom"])
            if not geom.isNull():
                band.addGeometry(geom, None)

        self.__restriction_band = band

    def __clear_restriction_band(self):
        """Очистить линию ограничений"""
        if self.__restriction_band:
            self.mapView.scene().removeItem(self.__restriction_band)
            self.__restriction_band = None

    def __open_about_dialog(self):
        self._show_info(
            """<html><body>
                    <p>В проекте используется набор иконок Fugue Icons.<br>
                    (C) 2013 <a href="https://p.yusukekamiyamane.com">Yusuke Kamiyamane</a>.
                    All rights reserved.</p>
                    <p>Лицензия: 
            <a href="https://creativecommons.org/licenses/by/3.0/">CC BY 3.0</a></p>
                    </body></html>
                    """,
            "О модуле"
        )