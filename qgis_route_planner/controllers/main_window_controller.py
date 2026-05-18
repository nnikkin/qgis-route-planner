from __future__ import annotations
from typing import TYPE_CHECKING

from qgis_route_planner.logger import Logger
from ..exceptions import DataImportError

if TYPE_CHECKING:
    from qgis_route_planner.models import MainWindowModel
    from qgis_route_planner.models import RestrictionModel
    from .settings_dialog_controller import SettingsDialogController
    from .restriction_dialog_controller import RestrictionDialogController
    from ..services import SpatialDataService, RoutingService, RestrictionService

from ..data import SelectedPointCollection, PointType

from qgis.PyQt.QtGui import QImage, QPainter
from qgis.PyQt.QtCore import pyqtSlot, pyqtSignal, QSize
from qgis.core import QgsPointXY, QgsMapSettings, QgsMapRendererCustomPainterJob, QgsGeometry

from .base_controller import BaseController

class MainWindowController(BaseController):
    """ Контроллер главного окна """

    layers_obtained = pyqtSignal(list)
    show_point_context_menu_requested = pyqtSignal(object, object)
    routes_display_requested = pyqtSignal(list)
    map_cleared = pyqtSignal()
    point_marker_add_requested = pyqtSignal(object)
    point_marker_remove_requested = pyqtSignal(int)
    point_marker_update_requested = pyqtSignal(int)

    select_point_on_map_requested = pyqtSignal(bool)
    restriction_point_added = pyqtSignal(int, float, float)

    restrictions_display_requested = pyqtSignal(list)
    restrictions_display_cleared = pyqtSignal()

    def __init__(
            self,
            model: MainWindowModel,
            restriction_model: RestrictionModel,
            settings_controller: SettingsDialogController,
            restr_controller: RestrictionDialogController,
            data_service: SpatialDataService,
            routing_service: RoutingService,
            restriction_service: RestrictionService,
    ):
        super().__init__()

        self.__model: MainWindowModel = model
        self.__restriction_model: RestrictionModel = restriction_model
        self.__settings_controller: SettingsDialogController = settings_controller
        self.__restr_controller: RestrictionDialogController = restr_controller
        self.__restr_controller.select_point_on_map_requested.connect(
            self.__on_map_selection_requested
        )
        self.__restriction_model.restrictions_changed.connect(
            self.__on_restrictions_changed
        )
        self.__restriction_model.current_restriction_id_changed.connect(
            self.__on_current_restriction_changed
        )

        self.__data_service: SpatialDataService = data_service
        self.__routing_service: RoutingService = routing_service
        self.__restriction_service: RestrictionService = restriction_service

        self.__current_route: SelectedPointCollection = SelectedPointCollection()

        self.__restriction_points: dict[int, tuple[float, float]] = {}
        self.__map_canvas = None

    def set_map_canvas(self, canvas):
        self.__map_canvas = canvas

    def open_settings_dialog(self, tab_index: int = 0):
        self.__settings_controller.open_dialog_tab(tab_index)

    def open_restriction_dialog(self):
        self.__restr_controller.open_dialog()

    @pyqtSlot(bool)
    def set_restrictions_visible(self, visible: bool):
        self.__model.restrictions_visible = visible
        if visible:
            self.__restr_controller.refresh_restrictions()
            self.__update_visible_restrictions()
            Logger.info("Ограничения отображаются на карте")
        else:
            Logger.info("Ограничения скрыты с карты")
            self.restrictions_display_cleared.emit()

    def initialize_map(self, schema: str = "routing", selected_layers: list | None = None):
        layers = self.__data_service.get_spatial_layers(schema=schema)
        if selected_layers:
            layers.extend(self.__data_service.get_selected_spatial_layers(selected_layers))
        if not layers:
            raise DataImportError(f"В схеме '{schema}' не обнаружены таблицы с геоданными")
        self.layers_obtained.emit(layers)

    @pyqtSlot(QgsPointXY)
    def on_map_point_selected(self, point: QgsPointXY):
        self.__routing_service.set_point_select_distance(self.__settings_controller.get_select_point_distance())
        snapped = self.__routing_service.snap_point_to_road(point)
        if not snapped:
            self.__model.status_message = "error:snap"
            return

        snapped_point, snap_info = snapped

        self.show_point_context_menu_requested.emit(snapped_point, snap_info)

    @pyqtSlot(QgsPointXY, PointType, object)
    def on_add_route_point(self, qgs_point_xy: QgsPointXY, point_type: PointType, snap_info):
        if not self.__model.active_profile:
            self.__model.status_message = "error:no_profile"
            return

        if not isinstance(snap_info, dict):
            snap_info = {"node_id": snap_info}

        node_id = snap_info.get("node_id")

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
        try:
            saved_path = self.__save_route_to_file(routes[route_index])
            if saved_path:
                self.__model.status_message = f"Маршрут сохранён: {saved_path}"
        except Exception as e:
            self.__model.status_message = f"Ошибка сохранения маршрута: {e}"

    def __save_route_to_file(self, route: list[dict]):
        """ Формирование HTML-файла с выбранным маршрутом """
        from qgis.PyQt.QtWidgets import QFileDialog
        import base64

        file_path, _ = QFileDialog.getSaveFileName(
            None,
            "Выберите место для сохранения файла",
            "",
            "HTML-файл (*.html)",
        )
        if not file_path:
            return

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
                action = "Продолжайте движение"
            name = edge.get("name") or ""
            dist = edge.get("length_m", 0)
            rows += f"""
            <tr>
                <td>{i + 1}</td>
                <td>{action}</td>
                <td>{name}</td>
                <td>{dist:.0f} м</td>
            </tr>"""

        # Экспорт карты в base64
        map_b64 = ""
        image = self.__export_route_image(route)
        if image and not image.isNull():
            from qgis.PyQt.QtCore import QBuffer, QByteArray, QIODevice
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.WriteOnly)
            image.save(buffer, "PNG")
            map_b64 = base64.b64encode(byte_array.data()).decode("utf-8")

        map_html = (
            f'<img src="data:image/png;base64,{map_b64}" style="width:100%;height:100%;object-fit:contain;" alt="Карта маршрута">'
            if map_b64 else
            '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#888;">Карта недоступна</div>'
        )

        html = f"""<!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Маршрут</title>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{ font-family: Arial, sans-serif; height: 100vh; display: flex; flex-direction: column; }}
            header {{ padding: 12px 20px; background: #f0f0f0; border-bottom: 1px solid #ccc; flex-shrink: 0; }}
            header h2 {{ font-size: 16px; margin-bottom: 4px; }}
            header .summary {{ font-size: 13px; color: #555; }}
            .content {{ display: flex; flex: 1; overflow: hidden; }}
            .map-panel {{ flex: 1; overflow: hidden; background: #e8e8e8; }}
            .table-panel {{ width: 420px; flex-shrink: 0; overflow-y: auto; border-left: 1px solid #ccc; }}
            table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
            th {{ background: #f0f0f0; border: 1px solid #ccc; padding: 7px 8px; text-align: left; position: sticky; top: 0; }}
            td {{ border: 1px solid #ddd; padding: 6px 8px; vertical-align: top; }}
            tr:nth-child(even) td {{ background: #fafafa; }}
        </style>
    </head>
    <body>
        <header>
            <h2>Маршрут</h2>
            <span class="summary">
                <b>Длина:</b> {total_distance:.2f} км &nbsp;|&nbsp;
                <b>Время:</b> {total_time:.0f} мин
            </span>
        </header>
        <div class="content">
            <div class="map-panel">{map_html}</div>
            <div class="table-panel">
                <table>
                    <thead>
                        <tr><th>#</th><th>Действие</th><th>Улица</th><th>Расстояние</th></tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </div>
    </body>
    </html>"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html)
        Logger.info(f"Файл сохранён: {file_path}")
        return file_path

    def __export_route_image(self, route: list[dict],
                           width: int = 1920, height: int = 1080) -> QImage:
        from qgis.PyQt.QtGui import QPen, QColor
        from qgis.PyQt.QtCore import QPointF

        extent = self.__get_route_extent(route)
        if extent is None or self.__map_canvas is None:
            return None

        extent.grow(extent.width() * 0.1)
        layers = self.__map_canvas.layers()

        settings = QgsMapSettings()
        settings.setLayers(layers)
        settings.setExtent(extent)
        settings.setOutputSize(QSize(width, height))
        white = QColor("white")
        settings.setBackgroundColor(white)

        image = QImage(QSize(width, height), QImage.Format_ARGB32)
        image.fill(white)

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
        return image

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
        start_node_id = point_ids[0] if point_ids else None
        end_node_id = point_ids[-1] if point_ids else None
        waypoint_ids = point_ids[1:-1] if point_ids else []
        restriction_node_ids = self.__restriction_service.get_active_restriction_node_ids(
            self.__model.active_profile
        )

        p1 = f"Запрошено построение маршрутов из точки {start_node_id} в точку {end_node_id}"
        p2 = f" с промежуточными точками {waypoint_ids}" if waypoint_ids else ""

        Logger.info(p1 + p2)

        routes = self.__routing_service.calculate_routes(
            start_node_id, end_node_id,
            self.__model.active_profile, waypoint_ids, restriction_node_ids, self.__current_route.points
        )

        if not routes:
            Logger.info("Маршруты не найдены")
            self.__model.status_message = "error:no_routes"
            self.__model.routes = []
            self.routes_display_requested.emit([])
            return

        Logger.info(f"Найдено маршрутов: {len(routes)}")
        self.__model.routes = routes
        self.__model.active_tab = 1
        self.routes_display_requested.emit(routes)

    @pyqtSlot(object)
    def update_active_profile(self, profile):
        """ Обновляет активный профиль в модели главного окна """
        self.__model.active_profile = profile

    @pyqtSlot(bool)
    def __on_map_selection_requested(self, active: bool = True):
        """ Запрос диалога ограничений """
        self.__model.restriction_select_mode = active

    def on_add_restriction_point(self, point: QgsPointXY, node_id: int):
        """ Добавить точку ограничения """
        self.__restriction_points[node_id] = (point.x(), point.y())
        self.restriction_point_added.emit(node_id, point.x(), point.y())
        self.__restr_controller.on_point_selected(point, node_id)
        self.__model.restriction_select_mode = False

    def cancel_add_restriction_point(self):
        self.__restriction_points.clear()
        self.__model.restriction_select_mode = False

    def clear_restriction_points(self):
        """ Очистить точки ограничений """
        self.__restriction_points.clear()

    def get_restriction_nodes(self) -> list[int]:
        """ Получить список узлов с ограничениями """
        return list(self.__restriction_points.keys())

    def snap_point(self, point: QgsPointXY):
        self.__routing_service.set_point_select_distance(self.__settings_controller.get_select_point_distance())
        return self.__routing_service.snap_point_to_road(point)

    def __on_restrictions_changed(self, _restrictions: list):
        self.__update_visible_restrictions()

    def __on_current_restriction_changed(self, _restriction_id: int | None):
        self.__update_visible_restrictions()

    def __update_visible_restrictions(self):
        if not self.__model.restrictions_visible:
            return

        selected_id = self.__restriction_model.current_restriction_id
        restriction_points = []

        for restriction in self.__restriction_model.restrictions:
            if restriction.node_id is None:
                continue
            coords = self.__routing_service.get_node_coordinates(restriction.node_id)
            if not coords:
                continue
            restriction_points.append({
                "id": restriction.id,
                "node_id": restriction.node_id,
                "x": coords[0],
                "y": coords[1],
                "selected": restriction.id == selected_id,
            })

        self.restrictions_display_requested.emit(restriction_points)
