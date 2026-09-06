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

    def has_required_points(self) -> bool:
        has_start = any(p.point_type == PointType.START for p in self.__points)
        has_end = any(p.point_type == PointType.END for p in self.__points)
        return has_start and has_end

    def __index_of(self, point_id: int) -> int:
        for i, p in enumerate(self.__points):
            if p.id == point_id:
                return i
        return -1

    def __reassign_endpoint_types(self):
        if not self.__points:
            return

        waypoint_order = 1
        for i, p in enumerate(self.__points):
            if i == 0:
                p.point_type = PointType.START
            elif i == len(self.__points) - 1 and len(self.__points) > 1:
                p.point_type = PointType.END
            else:
                p.point_type = PointType.WAYPOINT
                p.order = waypoint_order
                waypoint_order += 1

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
            fraction=fraction,
        )

        self.__next_point_id += 1

        if point_type == PointType.END:
            self.__points.append(route_point)
        elif point_type == PointType.START:
            self.__points.insert(0, route_point)
        else:
            end_idx = next((i for i, p in enumerate(self.__points) if p.point_type == PointType.END), None)
            if end_idx is not None:
                self.__points.insert(end_idx, route_point)
            else:
                self.__points.append(route_point)

        self.__reassign_endpoint_types()
        return route_point.id

    def remove_point(self, point_id: int) -> bool:
        idx = self.__index_of(point_id)
        if idx < 0:
            return False

        self.__points.pop(idx)
        self.__reassign_endpoint_types()
        return True

    def move_up(self, point_id: int) -> bool:
        """ Переместить точку выше в списке """
        idx = self.__index_of(point_id)
        if idx <= 0:
            return False

        self.__points[idx].order, self.__points[idx - 1].order = (
            self.__points[idx - 1].order, self.__points[idx].order
        )
        self.__points[idx - 1], self.__points[idx] = (
            self.__points[idx], self.__points[idx - 1]
        )
        self.__reassign_endpoint_types()
        return True

    def move_down(self, point_id: int) -> bool:
        """ Переместить точку ниже по списку """
        idx = self.__index_of(point_id)
        if idx < 0 or idx >= len(self.__points) - 1:
            return False

        self.__points[idx].order, self.__points[idx + 1].order = (
            self.__points[idx + 1].order, self.__points[idx].order
        )
        self.__points[idx], self.__points[idx + 1] = (
            self.__points[idx + 1], self.__points[idx]
        )
        self.__reassign_endpoint_types()
        return True

    def clear(self):
        self.__points.clear()
        self.__next_point_id = 1

    def get_point(self, point_id: int) -> RoutePoint | None:
        return next((p for p in self.__points if p.id == point_id), None)
