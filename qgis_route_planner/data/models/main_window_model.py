from qgis.PyQt.QtCore import QObject, pyqtSignal

from ..route import RoutePoint
from ..vehicle import VehicleProfile


class MainWindowModel(QObject):
    points_changed = pyqtSignal(list)

    routes_changed = pyqtSignal(list)
    active_route_changed = pyqtSignal(int)

    active_profile_changed = pyqtSignal(object)

    status_message_changed = pyqtSignal(str)
    active_tab_changed = pyqtSignal(int)
    clear_button_enabled_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self._points: list[RoutePoint] = []
        self._routes: list[list[dict]] = []
        self._active_route_index: int = 0
        self._active_profile: VehicleProfile | None = None
        self._status_message: str = ""
        self._active_tab: int = 0
        self._clear_button_enabled: bool = False

    @property
    def points(self) -> list[RoutePoint]:
        return self._points

    @points.setter
    def points(self, value: list[RoutePoint]):
        self._points = value
        self.points_changed.emit(self._points)
        self.clear_button_enabled = bool(self._points)

    @property
    def routes(self) -> list[list[dict]]:
        return self._routes

    @routes.setter
    def routes(self, value: list[list[dict]]):
        self._routes = value
        self.routes_changed.emit(self._routes)

    @property
    def active_route_index(self) -> int:
        return self._active_route_index

    @active_route_index.setter
    def active_route_index(self, value: int):
        self._active_route_index = value
        self.active_route_changed.emit(value)

    @property
    def active_profile(self) -> VehicleProfile | None:
        return self._active_profile

    @active_profile.setter
    def active_profile(self, value: VehicleProfile | None):
        self._active_profile = value
        self.active_profile_changed.emit(value)
        if value:
            self.status_message = f"Активный профиль: {value.name}"

    @property
    def status_message(self) -> str:
        return self._status_message

    @status_message.setter
    def status_message(self, value: str):
        self._status_message = value
        self.status_message_changed.emit(value)

    @property
    def active_tab(self) -> int:
        return self._active_tab

    @active_tab.setter
    def active_tab(self, value: int):
        self._active_tab = value
        self.active_tab_changed.emit(value)

    @property
    def clear_button_enabled(self) -> bool:
        return self._clear_button_enabled

    @clear_button_enabled.setter
    def clear_button_enabled(self, value: bool):
        self._clear_button_enabled = value
        self.clear_button_enabled_changed.emit(value)

    def clear(self):
        self.points = []
        self.routes = []
        self._active_route_index = 0
        self.active_tab = 0