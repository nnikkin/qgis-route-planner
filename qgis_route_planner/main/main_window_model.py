from qgis.PyQt.QtCore import QObject, pyqtSignal

from qgis_route_planner.main.active_profile_dto import ActiveProfileDto
from qgis_route_planner.main.point_dto import RoutePointDto


class MainWindowModel(QObject):
    """ Модель главного окна плагина PluginMainWindow """
    points_changed = pyqtSignal(list)

    routes_changed = pyqtSignal(list)
    active_route_changed = pyqtSignal(int)

    active_profile_changed = pyqtSignal(object)
    point_select_distance_changed = pyqtSignal(float)

    status_message_changed = pyqtSignal(str)
    active_tab_changed = pyqtSignal(int)
    clear_button_enabled_changed = pyqtSignal(bool)

    restriction_select_mode_activated = pyqtSignal(bool)
    restrictions_visible_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.__points: list[RoutePointDto] = []
        self.__routes: list[list[dict]] = []
        self.__active_route_index: int = 0
        self.__active_profile: ActiveProfileDto | None = None
        self.__point_select_distance: float = 10.0
        self.__status_message: str = ""
        self.__active_tab: int = 0
        self.__clear_button_enabled: bool = False
        self.__restriction_select_mode: bool = False
        self.__restrictions_visible: bool = False

    @property
    def points(self) -> list[RoutePointDto]:
        return self.__points

    @points.setter
    def points(self, value: list[RoutePointDto]):
        self.__points = value
        self.points_changed.emit(self.__points)
        self.clear_button_enabled = bool(self.__points)

    @property
    def routes(self) -> list[list[dict]]:
        return self.__routes

    @routes.setter
    def routes(self, value: list[list[dict]]):
        self.__routes = value
        self.routes_changed.emit(self.__routes)

    @property
    def active_route_index(self) -> int:
        return self.__active_route_index

    @active_route_index.setter
    def active_route_index(self, value: int):
        self.__active_route_index = value
        self.active_route_changed.emit(value)

    @property
    def active_profile(self) -> ActiveProfileDto | None:
        return self.__active_profile

    @active_profile.setter
    def active_profile(self, value: ActiveProfileDto | None):
        self.__active_profile = value
        self.active_profile_changed.emit(value)
        if value:
            self.status_message = f"Активный профиль: {value.name}"

    @property
    def point_select_distance(self) -> float:
        return self.__point_select_distance

    @point_select_distance.setter
    def point_select_distance(self, value: float):
        self.__point_select_distance = value
        self.point_select_distance_changed.emit(value)

    @property
    def status_message(self) -> str:
        return self.__status_message

    @status_message.setter
    def status_message(self, value: str):
        self.__status_message = value
        self.status_message_changed.emit(value)

    @property
    def active_tab(self) -> int:
        return self.__active_tab

    @active_tab.setter
    def active_tab(self, value: int):
        self.__active_tab = value
        self.active_tab_changed.emit(value)

    @property
    def clear_button_enabled(self) -> bool:
        return self.__clear_button_enabled

    @clear_button_enabled.setter
    def clear_button_enabled(self, value: bool):
        self.__clear_button_enabled = value
        self.clear_button_enabled_changed.emit(value)

    @property
    def restriction_select_mode(self) -> bool:
        return self.__restriction_select_mode

    @restriction_select_mode.setter
    def restriction_select_mode(self, value: bool):
        self.__restriction_select_mode = value
        self.restriction_select_mode_activated.emit(value)

    @property
    def restrictions_visible(self) -> bool:
        return self.__restrictions_visible

    @restrictions_visible.setter
    def restrictions_visible(self, value: bool):
        if self.__restrictions_visible != value:
            self.__restrictions_visible = value
            self.restrictions_visible_changed.emit(value)

    def clear(self):
        self.points = []
        self.routes = []
        self.__active_route_index = 0
        self.active_tab = 0
