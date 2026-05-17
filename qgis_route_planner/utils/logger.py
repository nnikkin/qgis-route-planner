from __future__ import annotations

import logging
from qgis.core import QgsMessageLog, Qgis

class Logger:
    @staticmethod
    def debug(msg: str, tag: str = ''):
        logging.getLogger().debug(msg)
        QgsMessageLog.logMessage(
            f"DEBUG: {msg}",
            "QgisRoutePlanner",
            Qgis.MessageLevel.NoLevel,
        )

    @staticmethod
    def info(msg: str):
        logging.getLogger().info(msg)
        QgsMessageLog.logMessage(
            msg,
            "QgisRoutePlanner",
            Qgis.MessageLevel.Info,
        )

    @staticmethod
    def warning(msg: str):
        logging.getLogger().warning(msg)
        QgsMessageLog.logMessage(
            msg,
            "QgisRoutePlanner",
            Qgis.MessageLevel.Warning,
        )

    @staticmethod
    def error(msg: str | Exception):
        logging.getLogger().error(msg)
        QgsMessageLog.logMessage(
            f"ERROR: {msg}",
            "QgisRoutePlanner",
            Qgis.MessageLevel.Warning,
        )

    @staticmethod
    def critical(msg: str):
        logging.getLogger().critical(msg)
        QgsMessageLog.logMessage(
            msg,
            "QgisRoutePlanner",
            Qgis.MessageLevel.Critical,
        )