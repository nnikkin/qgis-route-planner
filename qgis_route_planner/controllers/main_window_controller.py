from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QAction, QCursor
from qgis.PyQt.QtWidgets import QListWidgetItem, QMenu, QMessageBox

from qgis.core import QgsGeometry, QgsPointXY, QgsWkbTypes, QgsPalLayerSettings, QgsVectorLayerSimpleLabeling
from qgis.gui import QgsMapToolPan, QgsMapToolZoom, QgsRubberBand, QgsVertexMarker

from ..data.vehicle import VehicleProfile
from ..data.route import RoutePoint, PointType, SelectedPointCollection
from ..services import SpatialDataService, RoutingService
from ..views import PluginMainWindow
from ..views.widgets import SelectPointMapTool
from .settings_window_controller import SettingsWindowController


class MainWindowController:
    """Контроллер главного окна плагина"""

    def __init__(
            self,
            settings_controller: SettingsWindowController,
            db_service: SpatialDataService,
            routing_service: RoutingService,
            main_window: PluginMainWindow | None = None,
    ):
        self.__main_window: PluginMainWindow = main_window
        self.__settings_controller: SettingsWindowController = settings_controller
        self.__connected: bool = False

        self.__db_service = db_service
        self.__routing_service = routing_service

        self.__active_vehicle_profile: VehicleProfile = None
        self.__current_route: SelectedPointCollection = SelectedPointCollection()
        self.__current_route_result: list[dict] = []
        self.__current_routes_data: list[list[dict]] = []

        self.__point_markers: dict[int, QgsVertexMarker] = {}
        self.__route_bands: list[list[QgsRubberBand]] = []
        self.__temp_node_id: int = None

        self.__point_zoom_in = QgsMapToolZoom(self.__main_window.mapView, False)
        self.__point_zoom_out = QgsMapToolZoom(self.__main_window.mapView, True)
        self.__point_pan = QgsMapToolPan(self.__main_window.mapView)
        self.__point_select_tool = SelectPointMapTool(self.__main_window.mapView)
        self.__restr_edit_tool = SelectPointMapTool(self.__main_window.mapView)

        self.__connect_signals()

    def __connect_signals(self):
        # -- ГЛАВНОЕ МЕНЮ --
        self.__main_window.db_action.triggered.connect(self.__settings_controller.open_settings_dialog)
        self.__main_window.profiles_action.triggered.connect(lambda: self.__settings_controller.open_settings_dialog(1))
        self.__main_window.graph_action.triggered.connect(lambda: self.__settings_controller.open_settings_dialog(2))
        self.__main_window.about_action.triggered.connect(self.__open_about_dialog)

        # -- ИНСТРУМЕНТЫ КАРТЫ --
        self.__main_window.route_list_widget.route_selected.connect(self.__highlight_routes)
        self.__main_window.mapView.zoom_in_btn.clicked.connect(self.__zoom_in)
        self.__main_window.mapView.zoom_out_btn.clicked.connect(self.__zoom_out)
        self.__main_window.mapView.pan_btn.clicked.connect(self.__pan)
        self.__main_window.mapView.select_route_points_btn.clicked.connect(self.__activate_selection)
        #self.__main_window.mapView.activate_restr_mode_btn.clicked.connect(self.__)

        # -- ДРУГИЕ КНОПКИ ОКНА --
        self.__main_window.clear_list_button.clicked.connect(self.clear_everything)
        self.__point_select_tool.pointClicked.connect(self.__on_map_point_selected)
        #self.__restr_edit_tool.pointClicked.connect(lambda: self.__on_map_point_selected(restriction_mode=True))
        self.__main_window.route_list_widget.route_save_requested.connect(self.__save_route)

        self.__settings_controller.profile_changed.connect(
            self.__on_active_profile_changed
        )

        self.__settings_controller.profile_deleted.connect(
            self.__on_profile_deleted
        )

    def __open_about_dialog(self):
        QMessageBox.information(
            self.__main_window,
            "О модуле",
            """
                <html>
                <body>
                <p>В проекте используется набор иконок Fugue Icons.<br>
                (C) 2013 <a href="https://p.yusukekamiyamane.com">Yusuke Kamiyamane</a>. All rights reserved.</p>
                <p>These icons are licensed under a <a href="https://creativecommons.org/licenses/by/3.0/">Creative Commons Attribution 3.0 License.</a></p>
                </body>
                </html>
                """,
            QMessageBox.Ok
        )

    def clear_everything(self):
        self.clear_map()
        self.__clear_routes_list()
        self.__clear_points_list()
        self.__current_route.clear()

        self.__main_window.set_tab_active(0)

    def __clear_routes_list(self):
        self.__main_window.clear_routes_list()

    def __clear_points_list(self):
        self.__main_window.clear_points_list()

    def open_main_window(self):
        self.__main_window.show()

    def close_main_window(self):
        self.__main_window.close()

    def __activate_selection(self):
        self.__main_window.mapView.setMapTool(self.__point_select_tool)

    #def __activate_restr_mode(self):
    #    self.__main_window.mapView.setMapTool(self.__point_select_tool)

    def initialize_map(self, schema: str = "routing"):
        try:
            layers = self.__db_service.get_spatial_layers(schema=schema)
            if not layers:
                print(f"В схеме '{schema}' не обнаружены таблицы с геоданными!")
                return

            self.__main_window.mapView.set_layers(layers)

            for layer in layers:
                if 'graph_edges' in layer.name() and layer.fields().indexOf('name') >= 0:
                    settings = QgsPalLayerSettings()
                    settings.fieldName = 'name'
                    settings.enabled = True
                    labeling = QgsVectorLayerSimpleLabeling(settings)
                    layer.setLabelsEnabled(True)
                    layer.setLabeling(labeling)
                    layer.triggerRepaint()

            print("Слои загружены.")
        except Exception as e:
            print(f"Не удалось инициализировать виджет карты: {e}")

    def __on_map_point_selected(self, point: QgsPointXY):
        snapped = self.__routing_service.snap_point_to_road(point)
        if not snapped:
            QMessageBox.warning(
                self.__main_window,
                "Ошибка",
                "Не удалось привязать точку к дорожной сети.\nПожалуйста, выберите точку ближе к дороге.",
            )
            return

        point, node_id = snapped
        self.__temp_node_id = node_id

        self.__show_context_menu_for_point(point)

    def __show_context_menu_for_point(self, point: QgsPointXY):
        menu = QMenu(self.__main_window.mapView)
        current_point = point
        current_node_id = self.__temp_node_id
        has_start = any(p.point_type == PointType.START for p in self.__current_route.points)
        has_end = any(p.point_type == PointType.END for p in self.__current_route.points)

        start_available = not has_start
        end_available = has_start and not has_end
        waypoint_available = has_start

        actions = [
            ("Установить как начальную точку", PointType.START, start_available),
            ("Установить как промежуточную точку", PointType.WAYPOINT, waypoint_available),
            ("Установить как конечную точку", PointType.END, end_available)
        ]

        for title, point_type, is_enabled in actions:
            action = QAction(title, menu)
            action.triggered.connect(
                lambda checked=False, pt=point_type, cp=current_point: self.__add_route_point(cp, pt, current_node_id)
            )
            action.setEnabled(is_enabled)
            menu.addAction(action)

        menu.exec_(QCursor.pos())

    def __add_route_point(self, qgs_point_xy: QgsPointXY, point_type: PointType, node_id: int | None):
        if not self.__active_vehicle_profile:
            q = QMessageBox.question(
                self.__main_window,
                "Внимание",
                "Сначала создайте и выберите профиль транспортного средства, для которого будет произведён расчёт."
                "\nВы хотите перейти в настройки модуля?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if q == QMessageBox.Yes:
                self.__settings_controller.open_settings_dialog(1)
            return

        # Попытаемся найти ближайшую точку на графе
        if node_id is None:
            node_id = self.__routing_service.find_nearest_node(qgs_point_xy)

        # Если и там не нашли
        if node_id is None:
            QMessageBox.warning(
                self.__main_window,
                "Ошибка",
                "Не удалось найти ближайший узел дорожной сети.\nПожалуйста, выберите точку ближе к дороге.",
            )
            return

        self.__current_route.add_point(qgs_point_xy, point_type, node_id)
        route_point = self.__current_route.get_point(self.__current_route.next_point_id-1)
        self.__add_point_marker(route_point, point_type)
        self.__update_points_list()

        self.__try_build_routes()

    def __add_point_marker(self, route_point: RoutePoint, point_type: PointType):
        marker = QgsVertexMarker(self.__main_window.mapView)
        marker.setCenter(route_point.qgs_point_xy)
        marker.setIconType(QgsVertexMarker.IconType.ICON_CIRCLE)
        marker.setIconSize(10)
        marker.setPenWidth(3 if point_type in {PointType.START, PointType.END} else 2)
        self.__update_marker_color(route_point, marker)
        marker.show()
        self.__point_markers[route_point.id] = marker

    def __update_marker_color(self, route_point: RoutePoint, marker: QgsVertexMarker = None):
        marker = marker or self.__point_markers.get(route_point.id)
        if not marker:
            return

        if route_point.point_type == PointType.START:
            marker.setColor(Qt.green)
        elif route_point.point_type == PointType.END:
            marker.setColor(Qt.red)
        else:
            marker.setColor(Qt.black)

    def __update_points_list(self):
        self.__main_window.points_list_widget.clear()

        for route_point in self.__current_route.points:
            if route_point.point_type == PointType.START:
                prefix = "НАЧАЛО"
            elif route_point.point_type == PointType.END:
                prefix = "КОНЕЦ"
            else:
                prefix = f"Точка {route_point.order}"

            item = QListWidgetItem(f"{prefix}: ({route_point.qgs_point_xy.x():.6f}, {route_point.qgs_point_xy.y():.6f})")
            item.setData(Qt.ItemDataRole.UserRole, route_point.id)
            self.__main_window.points_list_widget.addItem(item)

        self.__main_window.clear_list_button.setEnabled(bool(self.__current_route.points))

    def __update_marker_for_point(self, point_id: int):
        point = self.__current_route.get_point(point_id)
        if point:
            self.__update_marker_color(point)

    def __display_routes(self, routes: list):
        self.__clear_route()
        if not routes:
            return

        self.__current_routes_data = routes
        extent = None

        for i, route in enumerate(routes):
            route_layers = []
            for edge in route:
                geom = QgsGeometry.fromWkt(edge["geom"])

                if geom.isNull():
                    continue

                route_band = QgsRubberBand(self.__main_window.mapView, QgsWkbTypes.LineGeometry)
                route_band.setColor(Qt.gray)
                route_band.setWidth(3)
                route_band.setToGeometry(geom, None)
                route_layers.append(route_band)

                if extent is None:
                    extent = geom.boundingBox()
                else:
                    extent.combineExtentWith(geom.boundingBox())

            self.__route_bands.append(route_layers)

        if extent:
            self.__main_window.mapView.setExtent(extent)

        self.__highlight_routes(0)
        self.__main_window.mapView.refresh()

    def __highlight_routes(self, route_to_highlight_idx: int):
        for i, layers in enumerate(self.__route_bands):
            for band in layers:
                band.setColor(Qt.darkGray if i != route_to_highlight_idx else Qt.blue)
                band.setWidth(3 if i != route_to_highlight_idx else 5)
                band.setZValue(0 if i != route_to_highlight_idx else 1)

        self.__main_window.mapView.refresh()

    def __show_route_info(self, route_order: int, route: list[dict]):
        info = self.__routing_service.get_route_info(route)
        self.__main_window.route_list_widget.add_page(route_order, route, info)

    def __clear_route(self):
        if self.__route_bands:
            for band_list in self.__route_bands:
                for band in band_list:
                    self.__main_window.mapView.scene().removeItem(band)
            self.__route_bands = []
        self.__current_routes_data = []
        self.__main_window.clear_routes_list()

    def __try_build_routes(self):
        if not self.__current_route.has_required_points():
            self.__clear_route()
            return

        self.__turn_off_map_tool()

        point_ids = self.__current_route.get_point_ids()
        waypoint_ids = point_ids[1:-1]
        start_node_id = point_ids[0]
        end_node_id = point_ids[-1]

        routes = self.__routing_service.calculate_routes(
            start_node_id,
            end_node_id,
            self.__active_vehicle_profile,
            waypoint_ids
        )
        if not routes:
            QMessageBox.information(
                self.__main_window,
                "",
                "Маршруты между выбранными точками не найдены.\n",
                QMessageBox.Ok
            )
            return
        else:
            self.__display_routes(routes)
            self.__main_window.clear_routes_list()
            self.__main_window.set_tab_active(1)

            for i, route in enumerate(routes):
                self.__show_route_info(i, route)


    def __remove_point(self, point_id: int):
        point = self.__current_route.remove_point(point_id)
        if not point:
            return

        marker = self.__point_markers.pop(point_id, None)
        if marker:
            self.__main_window.mapView.scene().removeItem(marker)

        self.__update_points_list()
        self.__try_build_routes()

    def clear_map(self):
        for marker in self.__point_markers.values():
            self.__main_window.mapView.scene().removeItem(marker)
        self.__point_markers.clear()
        self.__clear_route()
        self.__update_points_list()

    def __change_point_type(self, point_id: int, new_type: PointType):
        point = self.__current_route.change_point_type(point_id, new_type)
        if not point:
            return

        self.__update_marker_for_point(point_id)
        self.__update_points_list()
        self.__try_build_routes()

    def __get_active_profile(self):
        return self.__active_vehicle_profile

    def __on_active_profile_changed(self, profile: VehicleProfile | None):
        self.__active_vehicle_profile = profile

        if self.__active_vehicle_profile:
            self.__main_window.statusBar().showMessage(
                f"Активный профиль: {profile.name}"
            )

        if self.__current_route_result:
            self.__try_build_routes()

    def __on_profile_deleted(self, profile_id: int):
        if self.__active_vehicle_profile.id == profile_id:
            self.__active_vehicle_profile = None
            self.__main_window.statusBar().showMessage(
                "Профиль не выбран"
            )

    def __generate_instructions(self, route: list) -> str:
        """Генерирует текстовые инструкции по маршруту"""
        if not route:
            return "Нет инструкций"
        instructions = []
        total_distance = 0
        for i, edge in enumerate(route):
            total_distance += edge['cost']
            distance_km = total_distance / 1000
            if i == 0:
                action = "Старт"
            elif i == len(route) - 1:
                action = "Финиш"
            else:
                action = "Продолжать движение"

            instructions.append(f"""
            <tr>
                <td>{i + 1}.</td>
                <td>
                    <span font-size: 11px;">
                        Проехать: {distance_km:.2f} км
                    </span>
                </td>
            </tr>
            """)

        return "".join(instructions)

    def __save_route(self, route_index: int):
        if route_index < 0 or route_index >= len(self.__current_routes_data):
            return

        from qgis.PyQt.QtWidgets import QFileDialog

        route = self.__current_routes_data[route_index]
        file_url, filter = QFileDialog.getSaveFileUrl(
            self.__main_window,
            "Выберите место для сохранения файла",
            "",
            "HTML-файл (*.html)",
            None,
            QFileDialog.Option.ShowDirsOnly
        )

        if file_url is None:
            return


    # -- ИНСТРУМЕНТЫ ДЛЯ КАРТЫ --
    def __zoom_in(self):
        self.__main_window.mapView.setMapTool(self.__point_zoom_in)

    def __zoom_out(self):
        self.__main_window.mapView.setMapTool(self.__point_zoom_out)

    def __pan(self):
        self.__main_window.mapView.setMapTool(self.__point_pan)

    def __turn_off_map_tool(self):
        self.__main_window.mapView.setMapTool(None)