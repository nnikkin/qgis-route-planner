import logging
from qgis.core import QgsMessageLog, Qgis

class Logger:
    def __init__(self):
        self.__logger = logging.getLogger()

    def debug(self, msg: str, tag: str = ''):
        self.__logger.debug(msg)
        QgsMessageLog.logMessage(
            f"DEBUG: {msg}",
            "QgisRoutePlanner",
            Qgis.MessageLevel.NoLevel,
        )

    def info(self, msg: str):
        self.__logger.info(msg)
        QgsMessageLog.logMessage(
            msg,
            "QgisRoutePlanner",
            Qgis.MessageLevel.Info,
        )

    def warning(self, msg: str):
        self.__logger.warning(msg)
        QgsMessageLog.logMessage(
            msg,
            "QgisRoutePlanner",
            Qgis.MessageLevel.Warning,
        )

    def error(self, msg: str):
        self.__logger.error(msg)
        QgsMessageLog.logMessage(
            f"ERROR: {msg}",
            "QgisRoutePlanner",
            Qgis.MessageLevel.Warning,
        )

    def critical(self, msg: str):
        self.__logger.critical(msg)
        QgsMessageLog.logMessage(
            msg,
            "QgisRoutePlanner",
            Qgis.MessageLevel.Critical,
        )