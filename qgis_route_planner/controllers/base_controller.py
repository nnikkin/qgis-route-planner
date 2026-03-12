from qgis.PyQt.QtCore import QObject, pyqtSignal

class BaseController(QObject):
    show_error = pyqtSignal(str)
    show_warning = pyqtSignal(str)
    show_info = pyqtSignal(str)