from qgis.PyQt.QtCore import QObject, pyqtSignal

from qgis_route_planner.main.active_profile_dto import ActiveProfileDto
from qgis_route_planner.main.point_dto import RoutePointDto
from qgis_route_planner.routing import PointType


class MainWindowModel(QObject):
    """ Модель главного окна плагина PluginMainWindow """
    points_changed = pyqtSignal(list)
    selected_point_id_changed = pyqtSignal(object)

    routes_changed = pyqtSignal(list)
    active_route_changed = pyqtSignal(int)

    active_profile_changed = pyqtSignal(object)
    point_select_distance_changed = pyqtSignal(float)

    statusbar_message_changed = pyqtSignal(str)
    active_tab_changed = pyqtSignal(int)

    restriction_select_mode_activated = pyqtSignal(bool)
    restrictions_visible_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.__points: list[RoutePointDto] = []
        self.__routes: list[list[dict]] = []
        self.__selected_point_id: int | None = None
        self.__active_route_index: int = 0
        self.__active_profile: ActiveProfileDto | None = None
        self.__point_select_distance: float = 10.0
        self.__statusbar_message: str = ""
        self.__active_tab: int = 0
        self.__restriction_select_mode: bool = False
        self.__restrictions_visible: bool = False

    @property
    def points(self) -> list[RoutePointDto]:
        return self.__points

    @points.setter
    def points(self, value: list[RoutePointDto]):
        self.__points = value
        print(self.__points)
        print()
        self.points_changed.emit(self.__points)

    @property
    def routes(self) -> list[list[dict]]:
        return self.__routes

    @routes.setter
    def routes(self, value: list[list[dict]]):
        self.__routes = value
        self.routes_changed.emit(self.__routes)

    @property
    def selected_point_id(self) -> int | None:
        return self.__selected_point_id

    @selected_point_id.setter
    def selected_point_id(self, value: int | None):
        self.__selected_point_id = value
        self.selected_point_id_changed.emit(value)

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
        self.statusbar_message = f"Активное ТС: {value.name}" if value else f"Транспортное средство не задано!"

    @property
    def point_select_distance(self) -> float:
        return self.__point_select_distance

    @point_select_distance.setter
    def point_select_distance(self, value: float):
        self.__point_select_distance = value
        self.point_select_distance_changed.emit(value)

    @property
    def statusbar_message(self) -> str:
        return self.__statusbar_message

    @statusbar_message.setter
    def statusbar_message(self, value: str):
        self.__statusbar_message = value
        self.statusbar_message_changed.emit(value)

    @property
    def active_tab(self) -> int:
        return self.__active_tab

    @active_tab.setter
    def active_tab(self, value: int):
        self.__active_tab = value
        self.active_tab_changed.emit(value)

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

    def has_start_set(self) -> bool:
        return any(p.point_type == PointType.START for p in self.__points)

    def has_end_set(self) -> bool:
        return any(p.point_type == PointType.END for p in self.__points)

    def clear(self):
        self.points = []
        self.routes = []
        self.__active_route_index = 0
        self.active_tab = 0

    @staticmethod
    def route_point_to_dto(route_point) -> RoutePointDto:
        return RoutePointDto(
            id=route_point.id,
            point_type=route_point.point_type,
            order=route_point.order,
            x=route_point.qgs_point_xy.x(),
            y=route_point.qgs_point_xy.y(),
            address=route_point.address,
            node_id=route_point.node_id,
        )

    @staticmethod
    def profile_to_dto(profile) -> ActiveProfileDto | None:
        if profile is None:
            return None
        return ActiveProfileDto(
            id=getattr(profile, "id", None),
            name=getattr(profile, "name", ""),
        )