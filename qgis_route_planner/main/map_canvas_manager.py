from __future__ import annotations

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsPalLayerSettings,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis.gui import QgsRubberBand, QgsVertexMarker

from qgis_route_planner.routing.point_type import PointType
from qgis_route_planner.settings import SettingsService
from qgis_route_planner.layer_config.layer_role import LayerRole


class MapCanvasManager:
    """ Инкапсулирует временные визуальные объекты на QGIS canvas """

    def __init__(self, map_canvas):
        self.__map_canvas = map_canvas
        self.__point_markers: dict[int, QgsVertexMarker] = {}
        self.__route_bands: list[list[QgsRubberBand]] = []
        self.__restriction_markers: dict[int, QgsVertexMarker] = {}
        self.__visible_restriction_markers: dict[int, QgsVertexMarker] = {}

    def initialize_map(self, layers: list[QgsVectorLayer]):
        for layer in layers:
            self.__style_layer(layer)
            layer.triggerRepaint()
        display_layers = self.__with_basemap(layers)
        self.__map_canvas.set_layers(display_layers)
        self.__map_canvas.refresh()

    def add_point_marker(self, point):
        marker = QgsVertexMarker(self.__map_canvas)
        marker.setCenter(self.__graph_point_to_canvas(point.qgs_point_xy))
        marker.setIconType(QgsVertexMarker.IconType.ICON_CIRCLE)
        marker.setIconSize(10)
        marker.setPenWidth(
            3 if point.point_type in {PointType.START, PointType.END} else 2
        )
        self.__set_marker_color(marker, point.point_type)
        marker.show()
        self.__point_markers[point.id] = marker

    def remove_point_marker(self, point_id: int):
        marker = self.__point_markers.pop(point_id, None)
        if marker:
            self.__map_canvas.scene().removeItem(marker)

    def update_point_marker_color(self, point_id: int, point_type_name: str):
        marker = self.__point_markers.get(point_id)
        if marker:
            self.__set_marker_color(marker, point_type_name)

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
                geom = self.__graph_geometry_to_canvas(geom)
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

    def __create_restr_point_marker(self, canvas, x: float, y: float):
        marker = QgsVertexMarker(self.__map_canvas)
        marker.setCenter(self.__graph_point_to_canvas(QgsPointXY(x, y)))
        marker.setIconType(QgsVertexMarker.IconType.ICON_INVERTED_TRIANGLE)
        marker.setColor(Qt.red)
        marker.setIconSize(12)
        marker.setPenWidth(2)

        return marker

    def add_restriction_point_marker(self, node_id: int, x: float, y: float):
        marker = self.__create_restr_point_marker(self.__map_canvas, x, y)
        marker.show()
        self.__restriction_markers[node_id] = marker

    def clear_restriction_markers(self):
        for marker in self.__restriction_markers.values():
            self.__map_canvas.scene().removeItem(marker)
        self.__restriction_markers.clear()

    def display_visible_restrictions(self, restrictions: list[dict]):
        self.clear_visible_restriction_markers(refresh=False)
        for restriction in restrictions:
            marker_id = restriction.get("id") or restriction.get("node_id")
            if marker_id is None:
                continue

            marker = self.__create_restr_point_marker(self.__map_canvas, restriction["x"], restriction["y"])
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
        if layer.geometryType() == QgsWkbTypes.Polygon:
            self.__style_polygon_layer(layer)
        self.__enable_name_labels(layer)

    def __style_line_layer(self, layer: QgsVectorLayer):
        from qgis.core import QgsLineSymbol, QgsSimpleLineSymbolLayer

        symbol = QgsLineSymbol()
        symbol.deleteSymbolLayer(0)
        line = QgsSimpleLineSymbolLayer()
        if layer.name() == "graph_edges":
            line.setColor(Qt.black)
            line.setWidth(0.5)
        elif self.__layer_role(layer) == LayerRole.PIPING.name:
            line.setColor(QColor(20, 120, 190))
            line.setWidth(0.9)
        else:
            line.setColor(Qt.darkGray)
            line.setWidth(0.35)
        symbol.appendSymbolLayer(line)
        layer.renderer().setSymbol(symbol)

    def __style_point_layer(self, layer: QgsVectorLayer):
        from qgis.core import QgsMarkerSymbol

        symbol = QgsMarkerSymbol.createSimple({
            "name": "circle",
            "color": "190,70,70",
            "outline_color": "70,35,35",
            "size": "1.8",
        })
        layer.renderer().setSymbol(symbol)

    def __style_polygon_layer(self, layer: QgsVectorLayer):
        from qgis.core import QgsFillSymbol

        symbol = QgsFillSymbol()
        symbol.createSimple({
            "name": "polygon",
            "color": "255,191,0",
            "outline_color": "0,0,0",
            "size": "1",
        })
        layer.renderer().setSymbol(symbol)

    @staticmethod
    def __enable_name_labels(layer: QgsVectorLayer):
        from qgis.core import QgsVectorLayerSimpleLabeling

        label_field = None
        for field_name in ("name", "name_ru", "ref"):
            if layer.fields().indexOf(field_name) >= 0:
                label_field = field_name
                break
        if not label_field:
            return

        settings = QgsPalLayerSettings()
        settings.fieldName = label_field
        settings.enabled = True
        if hasattr(QgsPalLayerSettings, "Line"):
            settings.placement = QgsPalLayerSettings.Line
        layer.setLabelsEnabled(True)
        layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))

    @staticmethod
    def __set_marker_color(marker: QgsVertexMarker, point_type_str: str):
        colors = {
            PointType.START: Qt.green,
            PointType.END: Qt.magenta
        }
        marker.setColor(colors.get(point_type_str, Qt.black))

    @staticmethod
    def __with_basemap(layers: list[QgsVectorLayer]) -> list:
        from qgis.core import QgsRasterLayer

        settings = SettingsService().load_graph_settings()
        if not settings.get("basemap_enabled", False):
            return layers

        visible_layers = [
            layer for layer in layers
            if MapCanvasManager.__is_visible_with_basemap(layer)
        ]

        url = (settings.get("basemap_url") or "").strip()
        if not url:
            return visible_layers

        basemap = QgsRasterLayer(
            f"type=xyz&url={url}",
            "OpenStreetMap",
            "wms",
        )
        if basemap.isValid():
            basemap.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))
            return visible_layers + [basemap]
        return visible_layers

    @staticmethod
    def __is_visible_with_basemap(layer) -> bool:
        if not isinstance(layer, QgsVectorLayer):
            return True

        role = MapCanvasManager.__layer_role(layer)
        if role in {LayerRole.ROADS.name, LayerRole.PIPING.name}:
            return True
        return layer.name() == "graph_edges"

    @staticmethod
    def __layer_role(layer) -> str | None:
        role = layer.customProperty("qgis_route_planner/layer_role", None)
        return str(role) if role else None

    def __graph_point_to_canvas(self, point: QgsPointXY) -> QgsPointXY:
        graph_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        canvas_crs = self.__map_canvas.mapSettings().destinationCrs()
        if not canvas_crs.isValid() or canvas_crs == graph_crs:
            return point

        transform = QgsCoordinateTransform(graph_crs, canvas_crs, QgsProject.instance())
        return transform.transform(point)

    def __graph_geometry_to_canvas(self, geom: QgsGeometry) -> QgsGeometry:
        graph_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        canvas_crs = self.__map_canvas.mapSettings().destinationCrs()
        if not canvas_crs.isValid() or canvas_crs == graph_crs:
            return geom

        transformed = QgsGeometry(geom)
        transformed.transform(QgsCoordinateTransform(graph_crs, canvas_crs, QgsProject.instance()))
        return transformed
