from __future__ import annotations


class RoutingPluginError(Exception):
    pass

class TopologyBuildError(RoutingPluginError):
    """ Ошибка при построении топологии графа """
    pass

class NodeNotFoundError(RoutingPluginError):
    """ Узел не найден в графе """
    pass

class DbConnectionError(RoutingPluginError):
    def __init__(self, message: str, operation: str | None = None):
        super().__init__(message)
        self.operation = operation

class DataImportError(RoutingPluginError):
    """ Ошибка при импорте слоёв в граф """
    def __init__(self, message: str, layer_name: str | None = None):
        super().__init__(message)
        self.layer_name = layer_name

class ProfileOperationError(RoutingPluginError):
    def __init__(self, message: str, operation: str | None = None):
        super().__init__(message)
        self.operation = operation

class WeatherServiceError(RoutingPluginError):
    pass