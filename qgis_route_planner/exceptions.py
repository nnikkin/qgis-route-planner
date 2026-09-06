from __future__ import annotations

from qgis_route_planner.logger import Logger


class PluginError(Exception):
    def __init__(self, message: str, operation: str | None = None):
        super().__init__(message)
        self.operation = operation
        Logger.error(f"{operation}: {message}")

class TopologyBuildError(PluginError):
    """ Ошибка при построении топологии графа """
    pass

class NodeNotFoundError(PluginError):
    """ Узел не найден в графе """
    pass

class DbConnectionError(PluginError):
    pass

class DataImportError(PluginError):
    """ Ошибка при импорте слоёв в граф """
    pass

class ProfileOperationError(PluginError):
    pass

class WeatherServiceError(PluginError):
    pass