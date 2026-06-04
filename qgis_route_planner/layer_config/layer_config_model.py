from qgis.PyQt.QtCore import pyqtSignal, QObject

from layer_role import LayerRole


from dataclasses import dataclass
@dataclass
class Layer:
    name: str
    role: LayerRole


class LayerConfigModel(QObject):
    """ Модель, используемая LayerColumnsDialog """

    layers_changed = pyqtSignal(list)
    columns_changed = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.__selected_layers: list[Layer] = []

    @property
    def selected_layers(self) -> list[Layer]:
        return self.__selected_layers

    @selected_layers.setter
    def selected_layers(self, value: list[Layer]):
        self.__selected_layers = value
        self.layers_changed.emit(self.__selected_layers)

    def add_layer(self, name: str, role: LayerRole):
        self.__selected_layers.append(Layer(name, role))
        self.layers_changed.emit(self.__selected_layers)

    def pop_layer(self, index: int) -> Layer:
        layer = self.__selected_layers.pop(index)
        self.layers_changed.emit(self.__selected_layers)
        return layer

    def update_layer(self, layer: Layer, index: int):
        self.__selected_layers[index] = layer
        self.layers_changed.emit(self.__selected_layers)

    def clear(self):
        self.__selected_layers = []
        self.layers_changed.emit(self.__selected_layers)
