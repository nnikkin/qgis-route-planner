from __future__ import annotations

from ..data.models.main_window_model import MainWindowModel
from ..data.route import SelectedPointCollection, PointType
from ..services import SpatialDataService, RoutingService
from .settings_dialog_controller import SettingsDialogController

from qgis.PyQt import Qt
from qgis.PyQt.QtGui import QImage, QPainter
from qgis.PyQt.QtCore import QObject, pyqtSlot, pyqtSignal, QSize
from qgis.core import QgsPointXY, QgsMapSettings, QgsMapRendererCustomPainterJob, QgsGeometry


class MainWindowController(QObject):
    """Контроллер главного окна"""

    layers_obtained = pyqtSignal(list)
    show_point_context_menu_requested = pyqtSignal(object, int)
    routes_display_requested = pyqtSignal(list)
    map_cleared = pyqtSignal()
    point_marker_add_requested = pyqtSignal(object)
    point_marker_remove_requested = pyqtSignal(int)
    point_marker_update_requested = pyqtSignal(int)
    open_settings_requested = pyqtSignal(int)

    restriction_point_added = pyqtSignal(int, float, float)
    restriction_band_added = pyqtSignal(list)  # список точек для отображения
    restriction_band_cleared = pyqtSignal()

    def __init__(
            self,
            model: MainWindowModel,
            settings_controller: SettingsDialogController,
            db_service: SpatialDataService,
            routing_service: RoutingService,
    ):
        super().__init__()

        self.__model: MainWindowModel = model
        self.__settings_controller: SettingsDialogController = settings_controller

        self.__db_service: SpatialDataService = db_service
        self.__routing_service: RoutingService = routing_service

        self.__current_route: SelectedPointCollection = SelectedPointCollection()

        self.__restriction_points: dict[int, tuple[float, float]] = {}
        self.__restriction_band = None

    def open_settings_dialog(self, tab_index: int = 0):
        self.__settings_controller.open_dialog_tab(tab_index)

    def initialize_map(self, schema: str = "routing"):
        try:
            layers = self.__db_service.get_spatial_layers(schema=schema)
            if not layers:
                raise BaseException(f"В схеме '{schema}' не обнаружены таблицы с геоданными!")
            self.layers_obtained.emit(layers)
        except Exception as e:
            raise BaseException(f"Не удалось получить слои: {e}")

    @pyqtSlot(QgsPointXY)
    def on_map_point_selected(self, point: QgsPointXY):
        snapped = self.__routing_service.snap_point_to_road(point)
        if not snapped:
            self.__model.status_message = "error:snap"
            return

        snapped_point, node_id = snapped
        self.show_point_context_menu_requested.emit(snapped_point, node_id)

    @pyqtSlot(QgsPointXY, PointType, int)
    def on_add_route_point(self, qgs_point_xy: QgsPointXY, point_type: PointType, node_id: int):
        if not self.__model.active_profile:
            self.__model.status_message = "error:no_profile"
            return

        if node_id is None:
            node_id = self.__routing_service.find_nearest_node(qgs_point_xy)

        if node_id is None:
            self.__model.status_message = "error:no_node"
            return

        self.__current_route.add_point(qgs_point_xy, point_type, node_id)
        route_point = self.__current_route.get_point(self.__current_route.next_point_id - 1)

        self.__model.points = list(self.__current_route.points)
        self.point_marker_add_requested.emit(route_point)

        self.__try_build_routes()

    @pyqtSlot()
    def on_clear_everything(self):
        self.__current_route.clear()
        self.__model.clear()
        self.map_cleared.emit()

    @pyqtSlot(int)
    def on_route_selected(self, index: int):
        self.__model.active_route_index = index

    @pyqtSlot(int)
    def on_save_route(self, route_index: int):
        routes = self.__model.routes
        if route_index < 0 or route_index >= len(routes):
            return
        self.__save_route_to_file(routes[route_index])

    def __save_route_to_file(self, route: list[dict]):
        """Формирование HTML-файла с выбранным маршрутом"""
        # TODO: подключить к кнопке, сформировать файл с картинкой
        from qgis.PyQt.QtWidgets import QFileDialog

        file_url, _ = QFileDialog.getSaveFileUrl(
            None,
            "Выберите место для сохранения файла",
            "",
            "HTML-файл (*.html)",
        )
        if not file_url or file_url.isEmpty():
            return

        file_path = file_url.toLocalFile()
        if not file_path.endswith(".html"):
            file_path += ".html"

        total_distance = sum(e["length_m"] for e in route) / 1000
        total_time = sum(e["cost"] for e in route) / 60

        rows = ""
        for i, edge in enumerate(route):
            if i == 0:
                action = "Старт"
            elif i == len(route) - 1:
                action = "Финиш"
            else:
                action = "Продолжать движение"
            name = edge.get("name") or ""
            dist = edge.get("length_m", 0)
            rows += f"""
            <tr>
                <td>{i + 1}</td>
                <td>{action}</td>
                <td>{name}</td>
                <td>{dist:.0f} м</td>
            </tr>"""

        html = f"""
        <!DOCTYPE html>
        <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <title>Маршрут</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; }}
                    h2 {{ color: #333; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
                    th {{ background: #f0f0f0; }}
                    .summary {{ margin-bottom: 16px; }}
                </style>
            </head>
            <body>
                <h2>Маршрут</h2>
                <div class="summary">
                    <b>Длина:</b> {total_distance:.2f} км &nbsp;|&nbsp;
                    <b>Время:</b> {total_time:.0f} мин
                </div>
                <table>
                    <thead><tr><th>#</th><th>Действие</th><th></th><th>Расстояние</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            </body>
        </html>
        """

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)

    def export_route_image(self, route: list[dict], output_path: str,
                           width: int = 1920, height: int = 1080):
        from qgis.PyQt.QtGui import QPen, QColor
        from qgis.PyQt.QtCore import QPointF

        extent = self.__get_route_extent(route)
        if extent is None:
            return

        extent.grow(extent.width() * 0.1)
        layers = self.mapView.layers()

        settings = QgsMapSettings()
        settings.setLayers(layers)
        settings.setExtent(extent)
        settings.setOutputSize(QSize(width, height))
        settings.setBackgroundColor(Qt.white)

        image = QImage(QSize(width, height), QImage.Format_ARGB32)
        image.fill(Qt.white)

        painter = QPainter(image)

        # Рендерим фоновые слои
        job = QgsMapRendererCustomPainterJob(settings, painter)
        job.start()
        job.waitForFinished()

        # Рисуем маршрут поверх карты
        pen = QPen(QColor(0, 100, 255))
        pen.setWidth(4)
        painter.setPen(pen)

        transform = settings.mapToPixel()

        for edge in route:
            geom = QgsGeometry.fromWkt(edge["geom"])
            if geom.isNull():
                continue

            # Итерируем по вершинам линии
            vertices = list(geom.vertices())
            for i in range(len(vertices) - 1):
                p1 = transform.transform(vertices[i].x(), vertices[i].y())
                p2 = transform.transform(vertices[i + 1].x(), vertices[i + 1].y())
                painter.drawLine(
                    QPointF(p1.x(), p1.y()),
                    QPointF(p2.x(), p2.y())
                )

        painter.end()
        image.save(output_path)

    def __get_route_extent(self, route: list[dict]):
        from qgis.core import QgsGeometry
        extent = None
        for edge in route:
            geom = QgsGeometry.fromWkt(edge["geom"])
            if geom.isNull():
                continue
            bb = geom.boundingBox()
            extent = bb if extent is None else (extent.combineExtentWith(bb) or extent)
        return extent

    def __try_build_routes(self):
        if not self.__current_route.has_required_points():
            self.__model.routes = []
            self.routes_display_requested.emit([])
            return

        point_ids = self.__current_route.get_point_ids()
        start_node_id = point_ids[0]
        end_node_id = point_ids[-1]
        waypoint_ids = point_ids[1:-1]

        routes = self.__routing_service.calculate_routes(
            start_node_id, end_node_id,
            self.__model.active_profile, waypoint_ids
        )

        if not routes:
            self.__model.status_message = "error:no_routes"
            self.__model.routes = []
            self.routes_display_requested.emit([])
            return

        self.__model.routes = routes
        self.__model.active_tab = 1
        self.routes_display_requested.emit(routes)

    def on_add_restriction_point(self, point: QgsPointXY, node_id: int):
        """Добавить точку ограничения"""
        self.__restriction_points[node_id] = (point.x(), point.y())
        self.restriction_point_added.emit(node_id, point.x(), point.y())
        self.__update_restriction_band()

    def __update_restriction_band(self):
        """Обновить линию, соединяющую точки ограничений по графу"""
        if len(self.__restriction_points) < 2:
            if self.__restriction_band:
                self.restriction_band_cleared.emit()
            return

        node_ids = list(self.__restriction_points.keys())
        # Находим маршрут между точками
        routes = []
        for i in range(len(node_ids) - 1):
            route = self.__routing_service.calculate_routes(
                node_ids[i], node_ids[i + 1],
                self.__model.active_profile, []
            )
            if route:
                routes.extend(route[0])

        if routes:
            self.restriction_band_added.emit(routes)

    def clear_restriction_points(self):
        """Очистить точки ограничений"""
        self.__restriction_points.clear()
        self.restriction_band_cleared.emit()

    def get_restriction_nodes(self) -> list[int]:
        """Получить список узлов с ограничениями"""
        return list(self.__restriction_points.keys())