from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.gui import QgsMapCanvas, QgsMapToolEmitPoint, QgsVertexMarker
from qgis.core import QgsPointXY

class SelectPointMapTool(QgsMapToolEmitPoint):
    """Инструмент выбора точки маршрута на карте"""
    pointClicked = pyqtSignal(QgsPointXY)

    def __init__(self, canvas: QgsMapCanvas):
        self.__isEmittingPoint = None
        self.__endPoint = None
        self.__startPoint = None
        self.__canvas = canvas

        QgsMapToolEmitPoint.__init__(self, self.__canvas)
        self.__marker = QgsVertexMarker(self.__canvas)
        self.__marker.setIconType(QgsVertexMarker.IconType.ICON_X)
        self.__marker.setPenWidth(3)
        self.__marker.setColor(Qt.black)
        self.__marker.hide()

    def canvasPressEvent(self, e):
        point = self.toMapCoordinates(e.pos())
        self.__marker.setCenter(point)
        self.__marker.show()
        self.pointClicked.emit(point)

    def deactivate(self):
        self.__marker.hide()
        super().deactivate()