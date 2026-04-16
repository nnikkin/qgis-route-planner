from __future__ import annotations

from qgis.PyQt.QtCore import Qt
from qgis.core import (
    QgsGeometry,
    QgsMarkerSymbol,
    QgsPalLayerSettings,
    QgsVectorLayer,
    QgsVectorLayerSimpleLabeling,
    QgsWkbTypes,
)
from qgis.gui import QgsRubberBand, QgsVertexMarker

from qgis_route_planner.routing.point_type import PointType


class MapCanvasManager:
    """ Инкапсулирует временные визуальные объекты на QGIS canvas """

    def __init__(self, map_canvas):
        self.__map_canvas = map_canvas
        self.__point_markers: dict[int, QgsVertexMarker] = {}
        self.__route_bands: list[list[QgsRubberBand]] = []
        self.__restriction_markers: dict[int, QgsVertexMarker] = {}
        self.__visible_restriction_markers: dict[int, QgsVertexMarker] = {}

    def initialize_map(self, layers: list[QgsVectorLayer]):
        self.__map_canvas.set_layers(layers)
        for layer in layers:
            self.__style_layer(layer)
            layer.triggerRepaint()
        self.__map_canvas.refresh()

    def add_point_marker(self, route_point):
        marker = QgsVertexMarker(self.__map_canvas)
        marker.setCenter(route_point.qgs_point_xy)
        marker.setIconType(QgsVertexMarker.IconType.ICON_CIRCLE)
        marker.setIconSize(10)
        marker.setPenWidth(
            3 if route_point.point_type in {PointType.START, PointType.END} else 2
        )
        self.__set_marker_color(marker, route_point.point_type)
        marker.show()
        self.__point_markers[route_point.id] = marker

    def remove_point_marker(self, point_id: int):
        marker = self.__point_markers.pop(point_id, None)
        if marker:
            self.__map_canvas.scene().removeItem(marker)

    def update_point_marker_color(self, point_id: int, point_type: PointType):
        marker = self.__point_markers.get(point_id)
        if marker:
            self.__set_marker_color(marker, point_type)

    def display_routes(self, routes: list):
        self.clear_route_bands()
        if not routes:
            return

        extent = None
        for route in routes:
            band_list = []
            for edge in route:
                geom = QgsGeometry.fromWkt(edge["geom"])
                if geom.isNull():
                    continue
                band = QgsRubberBand(self.__map_canvas, QgsWkbTypes.LineGeometry)
                band.setColor(Qt.gray)
                band.setWidth(3)
                band.setToGeometry(geom, None)
                band_list.append(band)

                bb = geom.boundingBox()
                extent = bb if extent is None else (extent.combineExtentWith(bb) or extent)

            self.__route_bands.append(band_list)

        if extent:
            self.__map_canvas.setExtent(extent)

        self.highlight_routes(0)
        self.__map_canvas.refresh()

    def highlight_routes(self, active_index: int):
        for i, band_list in enumerate(self.__route_bands):
            is_active = i == active_index
            for band in band_list:
                band.setColor(Qt.blue if is_active else Qt.darkGray)
                band.setWidth(5 if is_active else 3)
                band.setZValue(1 if is_active else 0)
        self.__map_canvas.refresh()

    def clear_map_visuals(self):
        for marker in self.__point_markers.values():
            self.__map_canvas.scene().removeItem(marker)
        self.__point_markers.clear()
        self.clear_route_bands()

    def clear_route_bands(self):
        for band_list in self.__route_bands:
            for band in band_list:
                self.__map_canvas.scene().removeItem(band)
        self.__route_bands = []

    def add_restriction_point_marker(self, node_id: int, x: float, y: float):
        from qgis.core import QgsPointXY

        marker = QgsVertexMarker(self.__map_canvas)
        marker.setCenter(QgsPointXY(x, y))
        marker.setIconType(QgsVertexMarker.IconType.ICON_CROSS)
        marker.setColor(Qt.red)
        marker.setIconSize(12)
        marker.setPenWidth(2)
        marker.show()
        self.__restriction_markers[node_id] = marker

    def clear_restriction_markers(self):
        for marker in self.__restriction_markers.values():
            self.__map_canvas.scene().removeItem(marker)
        self.__restriction_markers.clear()

    def display_visible_restrictions(self, restrictions: list[dict]):
        from qgis.core import QgsPointXY

        self.clear_visible_restriction_markers(refresh=False)
        for restriction in restrictions:
            marker_id = restriction.get("id") or restriction.get("node_id")
            if marker_id is None:
                continue

            marker = QgsVertexMarker(self.__map_canvas)
            marker.setCenter(QgsPointXY(restriction["x"], restriction["y"]))
            marker.setIconType(QgsVertexMarker.IconType.ICON_CROSS)
            marker.setColor(Qt.darkMagenta if restriction.get("selected") else Qt.red)
            marker.setIconSize(14 if restriction.get("selected") else 10)
            marker.setPenWidth(3 if restriction.get("selected") else 2)
            marker.show()
            self.__visible_restriction_markers[marker_id] = marker

        self.__map_canvas.refresh()

    def clear_visible_restriction_markers(self, refresh: bool = True):
        for marker in self.__visible_restriction_markers.values():
            self.__map_canvas.scene().removeItem(marker)
        self.__visible_restriction_markers.clear()
        if refresh:
            self.__map_canvas.refresh()

    def __style_layer(self, layer: QgsVectorLayer):
        if layer.geometryType() == QgsWkbTypes.LineGeometry:
            self.__style_line_layer(layer)
        if layer.geometryType() == QgsWkbTypes.PointGeometry:
            self.__style_point_layer(layer)
        if layer.fields().indexOf("name") >= 0:
            self.__enable_name_labels(layer)

    def __style_line_layer(self, layer: QgsVectorLayer):
        from qgis.core import QgsLineSymbol, QgsSimpleLineSymbolLayer

        source = layer.dataProvider().dataSourceUri()
        is_routing = '"routing"' in source or "table=routing." in source

        symbol = QgsLineSymbol()
        symbol.deleteSymbolLayer(0)
        line = QgsSimpleLineSymbolLayer()
        line.setColor(Qt.black if is_routing else Qt.gray)
        line.setWidth(0.4 if is_routing else 0.2)
        symbol.appendSymbolLayer(line)
        layer.renderer().setSymbol(symbol)

    def __style_point_layer(self, layer: QgsVectorLayer):
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

    @staticmethod
    def __enable_name_labels(layer: QgsVectorLayer):
        settings = QgsPalLayerSettings()
        settings.fieldName = "name"
        settings.enabled = True
        if hasattr(QgsPalLayerSettings, "Line"):
            settings.placement = QgsPalLayerSettings.Line
        layer.setLabelsEnabled(True)
        layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))

    @staticmethod
    def __set_marker_color(marker: QgsVertexMarker, point_type: PointType):
        colors = {
            PointType.START: Qt.green,
            PointType.END: Qt.magenta,
            PointType.WAYPOINT: Qt.black,
            PointType.RESTRICTION: Qt.red,
        }
        marker.setColor(colors.get(point_type, Qt.black))
