# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..controllers import MainWindowController
    from qgis_route_planner.models import MainWindowModel

from qgis.PyQt import QtCore, QtWidgets
from qgis.PyQt.QtCore import pyqtSlot
from qgis.PyQt.QtWidgets import QAction, QMenu
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtCore import Qt

from qgis.core import (
    QgsGeometry, QgsPointXY, QgsWkbTypes, QgsVectorLayer,
    QgsPalLayerSettings, QgsVectorLayerSimpleLabeling,
    QgsMarkerSymbol
)
from qgis.gui import (
    QgsMapToolPan, QgsMapToolZoom, QgsRubberBand, QgsVertexMarker
)

from ..data.route import RoutePoint, PointType
from .widgets.map_widget import MapWidget
from .widgets.route_list_widget import RouteListWidget
from .message_box_mixin import MessageBoxMixin


class PluginMainWindow(QtWidgets.QMainWindow, MessageBoxMixin):
    """ Главное окно плагина """

    def __init__(self, model: MainWindowModel, controller: MainWindowController):
        super().__init__()

        self.__model: MainWindowModel = model
        self.__controller: MainWindowController = controller
        self.__restriction_dialog = None

        self.__point_markers: dict[int, QgsVertexMarker] = {}
        self.__route_bands: list[list[QgsRubberBand]] = []

        self.__restriction_markers: dict[int, QgsVertexMarker] = {}
        self.__restriction_band = None
        self.__visible_restriction_markers: dict[int, QgsVertexMarker] = {}

        self.__setupUi()

    def __setupUi(self):
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
        self.__controller.set_map_canvas(self.mapView)
        self.mapView.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        self.gridLayout_3.addWidget(self.mapView, 0, 0, 1, 1)
        self.setCentralWidget(self.central_widget)

        # Меню
        self.menubar = QtWidgets.QMenuBar(self)
        self.settings_menu = QtWidgets.QMenu("Настройки", self.menubar)
        self.view_menu = QtWidgets.QMenu("Вид", self.menubar)
        self.about_menu = QtWidgets.QMenu("Справка", self.menubar)

        self.db_action = QtWidgets.QAction("Подключение к базе данных", self)
        self.profiles_action = QtWidgets.QAction("Профили транспортных средств", self)
        self.graph_action = QtWidgets.QAction("Настройки графа дорог", self)
        self.weather_action = QtWidgets.QAction("Настройки сервиса погоды", self)
        self.show_restrictions_action = QtWidgets.QAction("Показывать точки ограничений", self)
        self.show_restrictions_action.setCheckable(True)
        self.about_action = QtWidgets.QAction("О модуле", self)

        self.settings_menu.addActions([self.db_action, self.profiles_action, self.graph_action, self.weather_action])
        self.view_menu.addAction(self.show_restrictions_action)
        self.about_menu.addAction(self.about_action)
        self.menubar.addMenu(self.settings_menu)
        self.menubar.addMenu(self.view_menu)
        self.menubar.addMenu(self.about_menu)
        self.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(self)
        self.setStatusBar(self.statusbar)

        self.__retranslateUi()
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(self)

        self.__setup_map_tools()
        self.__connect()

        self.mapView.show()

    def __retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "Поиск маршрутов"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Точки"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Маршруты"))
        self.clear_list_button.setText(_translate("MainWindow", "Построить новый маршрут"))
        self.settings_menu.setTitle(_translate("MainWindow", "Настройки"))
        self.view_menu.setTitle(_translate("MainWindow", "Вид"))
        self.about_menu.setTitle(_translate("MainWindow", "Справка"))
        self.about_action.setText(_translate("MainWindow", "О модуле"))
        self.profiles_action.setText(_translate("MainWindow", "Профили транспортных средств"))
        self.db_action.setText(_translate("MainWindow", "Подключение к базе данных"))
        self.graph_action.setText(_translate("MainWindow", "Настройки графа дорог"))
        self.weather_action.setText(_translate("MainWindow", "Настройки сервиса погоды"))
        self.show_restrictions_action.setText(_translate("MainWindow", "Показывать точки ограничений"))

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
        self.__model.clear_button_enabled_changed.connect(self.__on_clear_button_enabled_changed)
        self.__model.restriction_select_mode_activated.connect(self.__on_point_select_mode_changed)
        self.__model.restrictions_visible_changed.connect(self.__on_restrictions_visible_changed)

        self.__controller.layers_obtained.connect(self.__initialize_map)
        self.__controller.show_point_context_menu_requested.connect(self.__show_context_menu_for_point)
        self.__controller.routes_display_requested.connect(self.__display_routes)
        self.__controller.map_cleared.connect(self.__clear_map_visuals)
        self.__controller.point_marker_add_requested.connect(self.__add_point_marker)
        self.__controller.point_marker_remove_requested.connect(self.__remove_point_marker)
        self.__controller.point_marker_update_requested.connect(self.__update_point_marker_color)
        self.__controller.restriction_point_added.connect(self.__add_restriction_point_marker)
        self.__controller.restrictions_display_requested.connect(self.__display_visible_restrictions)
        self.__controller.restrictions_display_cleared.connect(self.__clear_visible_restriction_markers)

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
        self.weather_action.triggered.connect(
            lambda: self.__controller.open_settings_dialog(3)
        )
        self.show_restrictions_action.toggled.connect(
            self.__controller.set_restrictions_visible
        )
        self.about_action.triggered.connect(self.__open_about_dialog)

        self.mapView.zoom_in_btn.clicked.connect(lambda: self.mapView.setMapTool(self.__zoom_in_tool))
        self.mapView.zoom_out_btn.clicked.connect(lambda: self.mapView.setMapTool(self.__zoom_out_tool))
        self.mapView.pan_btn.clicked.connect(lambda: self.mapView.setMapTool(self.__pan_tool))
        self.mapView.select_route_points_btn.clicked.connect(
            lambda: self.mapView.setMapTool(self.__select_route_point_tool)
        )
        self.mapView.open_restriction_dialog_btn.clicked.connect(
            self.__controller.open_restriction_dialog
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
        """ Обрабатывает статусные сообщения и коды ошибок от контроллера """
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
                "Сначала нужно создать профиль транспортного средства, либо установить существующий в качестве активного."
                "\nВы хотите перейти в управление профилями?"
            )
            if q:
                self.__controller.open_settings_dialog(1)
        elif message in error_messages and error_messages[message]:
            self._show_warning(error_messages[message])
        else:
            self.statusBar().showMessage(message)

    @pyqtSlot(bool)
    def __on_clear_button_enabled_changed(self, enabled: bool):
        self.clear_list_button.setEnabled(
            enabled and not self.__model.restriction_select_mode
        )

    @pyqtSlot(bool)
    def __on_restrictions_visible_changed(self, visible: bool):
        self.show_restrictions_action.blockSignals(True)
        self.show_restrictions_action.setChecked(visible)
        self.show_restrictions_action.blockSignals(False)

    def __handle_restriction_selection(self, point: QgsPointXY, snap_info):
        node_id = snap_info.get("node_id") if isinstance(snap_info, dict) else snap_info
        self.__controller.on_add_restriction_point(point, node_id)

    @pyqtSlot(object, object)
    def __show_context_menu_for_point(self, point: QgsPointXY, snap_info):
        """ Показать контекстное меню точки """
        menu = QMenu(self.mapView)

        if self.__model.restriction_select_mode:
            action = QAction("Установить ограничение", menu)
            action.triggered.connect(
                lambda checked=False, p=point, s=snap_info:
                self.__handle_restriction_selection(p, s)
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
                    lambda checked=False, pt=point_type, p=point, s=snap_info:
                    self.__controller.on_add_route_point(p, pt, s)
                )
                action.setEnabled(enabled)
                menu.addAction(action)

        menu.exec_(QCursor.pos())

    @pyqtSlot(object)
    def __add_point_marker(self, route_point: RoutePoint):
        """ Добавить маркер на карту """
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
        """ Убрать маркер с карты """
        marker = self.__point_markers.pop(point_id, None)
        if marker:
            self.mapView.scene().removeItem(marker)

    @pyqtSlot(int)
    def __update_point_marker_color(self, point_id: int):
        """ Изменить цвет маркера """
        marker = self.__point_markers.get(point_id)
        if not marker:
            return
        point = next((p for p in self.__model.points if p.id == point_id), None)
        if point:
            self.__set_marker_color(marker, point.point_type)

    @pyqtSlot(list)
    def __display_routes(self, routes: list):
        """ Метод для отображения маршрутов на карте """
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
        """ Подсветка маршрута """
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
        self.mapView.set_layers(layers)
        for layer in layers:
            if layer.geometryType() == QgsWkbTypes.LineGeometry:
                from qgis.core import QgsSimpleLineSymbolLayer, QgsLineSymbol

                source = layer.dataProvider().dataSourceUri()
                is_routing = '"routing"' in source or 'table=routing.' in source

                symbol = QgsLineSymbol()
                symbol.deleteSymbolLayer(0)
                line = QgsSimpleLineSymbolLayer()

                if is_routing:
                    line.setColor(Qt.black)  # граф
                    line.setWidth(0.4)
                else:
                    line.setColor(Qt.gray)  # исходные данные
                    line.setWidth(0.2)

                symbol.appendSymbolLayer(line)
                layer.renderer().setSymbol(symbol)

            if layer.geometryType() == QgsWkbTypes.PointGeometry:
                source = layer.dataProvider().dataSourceUri().lower()
                layer_name = layer.name().lower()
                is_graph_nodes = "graph_nodes" in layer_name or "graph_nodes" in source
                symbol = QgsMarkerSymbol.createSimple({
                    "name": "circle",
                    "color": "190,70,70" if is_graph_nodes else "0,0,0",
                    "outline_color": "70,35,35" if is_graph_nodes else "0,0,0",
                    "size": "1.8" if is_graph_nodes else "0.5",
                })
                layer.renderer().setSymbol(symbol)

            if layer.fields().indexOf('name') >= 0:
                settings = QgsPalLayerSettings()
                settings.fieldName = 'name'
                settings.enabled = True
                if hasattr(QgsPalLayerSettings, "Line"):
                    settings.placement = QgsPalLayerSettings.Line
                layer.setLabelsEnabled(True)
                layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))

            layer.triggerRepaint()
        self.mapView.refresh()

    def __set_marker_color(self, marker: QgsVertexMarker, point_type: PointType):
        """ Установить цвет маркера """
        colors = {
            PointType.START: Qt.green,
            PointType.END: Qt.magenta,
            PointType.WAYPOINT: Qt.black,
            PointType.RESTRICTION: Qt.red
        }
        marker.setColor(colors.get(point_type, Qt.black))

    def __get_route_info(self, route: list[dict]) -> dict:
        """ Получить информацию по маршруту """
        if not route:
            return {'distance_km': 0, 'time_minutes': 0, 'segments': 0}
        return {
            'distance_km': sum(e['length_m'] for e in route) / 1000,
            'time_minutes': sum(e['cost'] for e in route) / 60,
            'segments': len(route),
        }

    @pyqtSlot(bool)
    def __on_point_select_mode_changed(self, active: bool):
        self.__set_main_ui_locked(active)
        if active:
            self.__activate_restriction_mode()
        else:
            self.__deactivate_restriction_mode()

    def __activate_restriction_mode(self):
        """ Активировать режим выбора точек для ограничений """
        self.raise_()
        self.mapView.setMapTool(self.__select_restriction_point_tool)

    def __deactivate_restriction_mode(self):
        """ Деактивировать режим выбора точек для ограничений """
        self.mapView.unsetMapTool(self.__select_restriction_point_tool)
        self.__clear_restriction_markers()

    def __cancel_restriction_selection(self):
        self.__deactivate_restriction_mode()
        self.__controller.cancel_add_restriction_point()

    def __add_restriction_point_marker(self, node_id: int, x: float, y: float):
        """ Добавить маркер точки ограничения на карту """
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

    def __clear_restriction_markers(self):
        """ Очистить точку ограничения с карты """
        if self.__restriction_markers:
            for node_id, marker in list(self.__restriction_markers.items()):
                self.mapView.scene().removeItem(marker)
            self.__restriction_markers.clear()

    @pyqtSlot(list)
    def __display_visible_restrictions(self, restrictions: list[dict]):
        self.__clear_visible_restriction_markers()
        for restriction in restrictions:
            marker_id = restriction.get("id") or restriction.get("node_id")
            if marker_id is None:
                continue

            marker = QgsVertexMarker(self.mapView)
            marker.setCenter(QgsPointXY(restriction["x"], restriction["y"]))
            marker.setIconType(QgsVertexMarker.IconType.ICON_CROSS)
            marker.setColor(
                Qt.darkMagenta if restriction.get("selected") else Qt.red
            )
            marker.setIconSize(14 if restriction.get("selected") else 10)
            marker.setPenWidth(3 if restriction.get("selected") else 2)
            marker.show()
            self.__visible_restriction_markers[marker_id] = marker

        self.mapView.refresh()

    def __clear_visible_restriction_markers(self):
        for marker in self.__visible_restriction_markers.values():
            self.mapView.scene().removeItem(marker)
        self.__visible_restriction_markers.clear()
        self.mapView.refresh()

    def __set_main_ui_locked(self, locked: bool):
        for menu in (self.settings_menu, self.view_menu, self.about_menu):
            menu.setEnabled(not locked)

        for widget in (
                self.tabWidget,
                self.mapView.zoom_in_btn,
                self.mapView.zoom_out_btn,
                self.mapView.pan_btn,
                self.mapView.select_route_points_btn,
                self.mapView.open_restriction_dialog_btn,
        ):
            widget.setEnabled(not locked)

        self.__on_clear_button_enabled_changed(self.__model.clear_button_enabled)

    def __open_about_dialog(self):
        self._show_info(
            """<html><body>
                    <p>В проекте используется набор иконок Fugue Icons.<br>
                    (C) 2013 <a href="https://p.yusukekamiyamane.com">Yusuke Kamiyamane</a>. All rights reserved.</p>
                    <p>Лицензия 
            <a href="https://creativecommons.org/licenses/by/3.0/">CC BY 3.0</a></p>
                    <hr>
                    <p>Сервис погоды предоставлен <a href="https://openweathermap.org/">OpenWeatherMap.</a></p>
                    <p>Бесплатный тариф OpenWeatherMap предоставляется под лицензией <a href="http://opendatacommons.org/licenses/odbl/1.0/">ODbL (Open Database License)</a>.</p>
                    </body></html>
                    """,
            "О модуле"
        )
