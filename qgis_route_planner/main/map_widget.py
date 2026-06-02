from qgis.PyQt.QtGui import QIcon, QPixmap
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QVBoxLayout, QPushButton, QWidget

from qgis.core import (
    QgsVectorLayer,
    QgsRectangle
)
from qgis.gui import (
    QgsMapCanvas
)

from qgis_route_planner import resources


class MapWidget(QgsMapCanvas):
    """ Виджет карты для главного окна """

    def __init__(self):
        super().__init__()
        self.__layers = []

        self.setObjectName("mapWidget")
        self.setCanvasColor(Qt.white)
        self.enableAntiAliasing(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # создание управления картой
        self.__map_controls = QWidget(self)
        self.__map_controls.setStyleSheet("background: rgba(255,255,255,180);")
        self.__btns_layout = QVBoxLayout(self.__map_controls)

        self.__btn_zoom_in = QPushButton(self)
        self.__btn_zoom_in.setIcon(QIcon(QPixmap(":map_icons/map_zoomin")))
        self.__btn_zoom_in.setToolTip("Увеличить масштаб")

        self.__btn_zoom_out = QPushButton(self)
        self.__btn_zoom_out.setIcon(QIcon(QPixmap(":map_icons/map_zoomout")))
        self.__btn_zoom_out.setToolTip("Уменьшить масштаб")

        self.__btn_pan_mode = QPushButton(self)
        self.__btn_pan_mode.setIcon(QIcon(QPixmap(":map_icons/map_move")))
        self.__btn_pan_mode.setToolTip("Включить перемещение по карте")

        self.__btn_select_points_mode = QPushButton(self)
        self.__btn_select_points_mode.setIcon(QIcon(QPixmap(":map_icons/map_add_point")))
        self.__btn_select_points_mode.setToolTip("Выбрать точки маршрута")

        self.__btn_open_restriction_dialog = QPushButton(self)
        self.__btn_open_restriction_dialog.setIcon(QIcon(QPixmap(":map_icons/map_restrict")))
        self.__btn_open_restriction_dialog.setToolTip("Задать ограничения")

        for btn in (self.__btn_zoom_in, self.__btn_pan_mode, self.__btn_zoom_out, self.__btn_select_points_mode,
                    self.__btn_open_restriction_dialog):
            btn.setFixedSize(30, 30)
            btn.setContentsMargins(0, 0, 0, 30)
            self.__btns_layout.addWidget(btn)

        self.__map_controls.adjustSize()

    @property
    def zoom_in_btn(self):
        return self.__btn_zoom_in

    @property
    def zoom_out_btn(self):
        return self.__btn_zoom_out

    @property
    def pan_btn(self):
        return self.__btn_pan_mode

    @property
    def select_route_points_btn(self):
        return self.__btn_select_points_mode

    @property
    def open_restriction_dialog_btn(self):
        return self.__btn_open_restriction_dialog

    def set_layers(self, layers: list):
        """ Устанавливает слои на карту """
        self.__layers = layers
        self.setLayers(layers)

        extent = QgsRectangle()
        for layer in self.__layers:
            if not layer or not layer.isValid():
                continue

            layer_extent = layer.extent()
            if layer_extent.isEmpty():
                continue

            if extent.isEmpty():
                extent = QgsRectangle(layer_extent)
            else:
                extent.combineExtentWith(layer_extent)

        if not extent.isEmpty():
            self.setExtent(extent)

        self.refresh()

    def add_layer(self, layer: QgsVectorLayer):
        """ Добавляет слой """
        current_layers = self.__layers
        current_layers.append(layer)
        self.set_layers(current_layers)
