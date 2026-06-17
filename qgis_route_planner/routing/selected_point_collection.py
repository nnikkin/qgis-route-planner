from __future__ import annotations

from qgis.core import QgsPointXY

from .point_type import PointType
from .route_point import RoutePoint


class SelectedPointCollection:
    """ Коллекция точек, выбранных для расчёта маршрута """

    def __init__(self):
        self.__points: list = []
        self.__next_point_id = 1

    @property
    def points(self) -> list:
        return self.__points

    def get_routing_node_ids(self) -> list[int]:
        return [p.node_id for p in self.__points]

    def has_start(self):
        return any(p.point_type == PointType.START for p in self.__points)

    def has_end(self):
        return any(p.point_type == PointType.END for p in self.__points)

    def has_required_points(self) -> bool:
        return self.has_start() and self.has_end()

    def __index_of(self, point_id: int) -> int:
        for i, p in enumerate(self.__points):
            if p.id == point_id:
                return i
        return -1

    def add_point(
            self,
            qgs_point_xy: QgsPointXY,
            point_type: PointType,
            node_id: int = None,
            edge_id: int = None,
            fraction: float = None,
    ) -> int :
        if not qgs_point_xy or not point_type or (node_id is None and edge_id is None):
            raise Exception("Для добавления требуются координаты, тип и привязка к дороге")

        route_point = RoutePoint(
            id=self.__next_point_id,
            qgs_point_xy=qgs_point_xy,
            point_type=point_type,
            node_id=node_id,
            edge_id=edge_id,
            fraction=fraction
        )

        self.__next_point_id += 1

        if point_type == PointType.END:
            self.__points.append(route_point)
        elif point_type == PointType.START:
            self.__points.insert(0, route_point)
        else:
            if self.has_start() and not self.has_end():
                self.__points.append(route_point)
            else:
                self.__points.insert(-1, route_point)

        self.__reorder()
        return route_point.id

    def __reorder(self):
        for i, point in enumerate(self.__points):
            point.order = i

    def remove_point(self, point_id: int) -> bool:
        idx = self.__index_of(point_id)
        if idx < 0:
            return False

        self.__points.pop(idx)
        self.__reorder()
        return True

    def move_up(self, point_id: int) -> bool:
        """ Переместить точку выше в списке """
        idx = self.__index_of(point_id)
        if idx <= 0:
            return False

        self.__points[idx].point_type, self.__points[idx - 1].point_type = (
            self.__points[idx - 1].point_type, self.__points[idx].point_type
        )
        self.__points[idx - 1], self.__points[idx] = (
            self.__points[idx], self.__points[idx - 1]
        )
        self.__reorder()
        return True

    def move_down(self, point_id: int) -> bool:
        """ Переместить точку ниже по списку """
        idx = self.__index_of(point_id)
        if idx < 0 or idx >= len(self.__points) - 1:
            return False

        self.__points[idx].point_type, self.__points[idx + 1].point_type = (
            self.__points[idx + 1].point_type, self.__points[idx].point_type
        )
        self.__points[idx], self.__points[idx + 1] = (
            self.__points[idx + 1], self.__points[idx]
        )
        self.__reorder()
        return True

    def clear(self):
        self.__points.clear()
        self.__next_point_id = 1

    def get_point(self, point_id: int) -> RoutePoint | None:
        return next((p for p in self.__points if p.id == point_id), None)
