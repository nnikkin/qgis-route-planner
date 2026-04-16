from __future__ import annotations

import base64

from qgis.PyQt.QtCore import QBuffer, QByteArray, QIODevice, QPointF, QSize
from qgis.PyQt.QtGui import QColor, QImage, QPainter, QPen
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.core import QgsGeometry, QgsMapRendererCustomPainterJob, QgsMapSettings

from qgis_route_planner.logger import Logger


class RouteExportService:
    """Формирует HTML-файл с описанием маршрута и снимком карты."""

    def save_route(self, route: list[dict], map_canvas) -> str | None:
        file_path, _ = QFileDialog.getSaveFileName(
            None,
            "Выберите место для сохранения файла",
            "",
            "HTML-файл (*.html)",
        )
        if not file_path:
            return None

        if not file_path.endswith(".html"):
            file_path += ".html"

        html = self.__build_html(route, self.__export_route_image(route, map_canvas))
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(html)

        Logger.info(f"Файл сохранён: {file_path}")
        return file_path

    def __build_html(self, route: list[dict], image: QImage | None) -> str:
        total_distance = sum(edge["length_m"] for edge in route) / 1000
        total_time = sum(edge["cost"] for edge in route) / 60

        rows = ""
        for index, edge in enumerate(route):
            if index == 0:
                action = "Старт"
            elif index == len(route) - 1:
                action = "Финиш"
            else:
                action = "Продолжайте движение"

            rows += f"""
            <tr>
                <td>{index + 1}</td>
                <td>{action}</td>
                <td>{edge.get("name") or ""}</td>
                <td>{edge.get("length_m", 0):.0f} м</td>
            </tr>"""

        map_html = self.__map_html(image)
        return f"""<!DOCTYPE html>
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

    @staticmethod
    def __map_html(image: QImage | None) -> str:
        if image is None or image.isNull():
            return '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#888;">Карта недоступна</div>'

        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.WriteOnly)
        image.save(buffer, "PNG")
        map_b64 = base64.b64encode(byte_array.data()).decode("utf-8")
        return f'<img src="data:image/png;base64,{map_b64}" style="width:100%;height:100%;object-fit:contain;" alt="Карта маршрута">'

    def __export_route_image(
            self,
            route: list[dict],
            map_canvas,
            width: int = 1920,
            height: int = 1080,
    ) -> QImage | None:
        extent = self.__get_route_extent(route)
        if extent is None or map_canvas is None:
            return None

        extent.grow(extent.width() * 0.1)

        settings = QgsMapSettings()
        settings.setLayers(map_canvas.layers())
        settings.setExtent(extent)
        settings.setOutputSize(QSize(width, height))
        white = QColor("white")
        settings.setBackgroundColor(white)

        image = QImage(QSize(width, height), QImage.Format_ARGB32)
        image.fill(white)

        painter = QPainter(image)
        job = QgsMapRendererCustomPainterJob(settings, painter)
        job.start()
        job.waitForFinished()

        pen = QPen(QColor(0, 100, 255))
        pen.setWidth(4)
        painter.setPen(pen)

        transform = settings.mapToPixel()
        for edge in route:
            geom = QgsGeometry.fromWkt(edge["geom"])
            if geom.isNull():
                continue

            vertices = list(geom.vertices())
            for index in range(len(vertices) - 1):
                p1 = transform.transform(vertices[index].x(), vertices[index].y())
                p2 = transform.transform(vertices[index + 1].x(), vertices[index + 1].y())
                painter.drawLine(QPointF(p1.x(), p1.y()), QPointF(p2.x(), p2.y()))

        painter.end()
        return image

    @staticmethod
    def __get_route_extent(route: list[dict]):
        extent = None
        for edge in route:
            geom = QgsGeometry.fromWkt(edge["geom"])
            if geom.isNull():
                continue
            bb = geom.boundingBox()
            extent = bb if extent is None else (extent.combineExtentWith(bb) or extent)
        return extent
