import os

from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QApplication

from .plugin_coordinator import PluginCoordinator


class QgisRoutePlanner:

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = self.tr(u"&Поиск маршрутов")
        self.first_start = True
        self.icon_path = f":/plugins/qgis_route_planner/plugin_icon"

        app = QApplication.instance()
        #if app:
        #    app.setWindowIcon(QIcon(self.icon_path))

        self.__orchestrator: PluginCoordinator = PluginCoordinator()
        self.__orchestrator.plugin_initialized.connect(self.__on_initialized)
        self.__orchestrator.plugin_init_cancelled.connect(self.__on_init_cancelled)
        self.__orchestrator.crit_plugin_error.connect(self.unload)

        from qgis.PyQt.QtCore import QLibraryInfo
        locale = QSettings().value("locale/userLocale", "ru")
        locale_path = os.path.join(self.plugin_dir, "i18n", f"QgisRoutePlanner_{locale}.qm")
        self.__install_translator(locale_path)

        qt_translations_path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
        qt_locale_path = os.path.join(qt_translations_path, f"qtbase_{locale.split('_')[0]}.qm")
        self.__install_translator(qt_locale_path)

    def __install_translator(self, locale_path: str):
        try:
            if os.path.exists(locale_path):
                self.__plugin_translator = QTranslator()
                self.__plugin_translator.load(locale_path)
                QCoreApplication.installTranslator(self.__plugin_translator)
        except Exception as e:
            print(e)

    def tr(self, message):
        return QCoreApplication.translate("QgisRoutePlanner", message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None,
    ):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)
        if whats_this is not None:
            action.setWhatsThis(whats_this)
        if add_to_toolbar:
            self.iface.addToolBarIcon(action)
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)
        return action

    def initGui(self):
        self.add_action(
            self.icon_path,
            text=self.tr(u"Открыть модуль поиска маршрутов"),
            callback=self.run,
            parent=self.iface.mainWindow(),
        )
        self.first_start = True

    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u"&Поиск маршрутов"), action)
            self.iface.removeToolBarIcon(action)

        self.__orchestrator.unload()

    def run(self):
        if self.first_start:
            self.first_start = False
            self.__orchestrator.first_start_initialize()
        else:
            self.__orchestrator.open_main_window()

    def __on_initialized(self):
        self.first_start = False

    def __on_init_cancelled(self):
        self.first_start = True
