from qgis.core import QgsPointXY

from . import PointType, RoutePoint
from ...utils import DoublyLinkedList


class SelectedPointCollection:
    """Коллекция точек, выбранных для расчёта маршрута."""

    def __init__(self):
        self.__points: DoublyLinkedList = DoublyLinkedList()
        self.__next_point_id = 1

    @property
    def points(self) -> DoublyLinkedList:
        return self.__points

    @property
    def next_point_id(self) -> int:
        return self.__next_point_id

    def get_point_ids(self) -> list[int]:
        return [p.node_id for p in self.__points]

    def has_start(self) -> bool:
        pass

    def has_end(self) -> bool:
        pass

    def has_required_points(self) -> bool:
        pass

    def _reindex(self):
        """Обновляет поле order у каждой точки согласно их позиции в списке."""
        for index, point in enumerate(self.__points):
            point.order = index

    def _insert_order(self, point_type: PointType) -> int:
        """Определяет порядковый номер для новой точки."""
        if point_type == PointType.START:
            return -1

        if point_type == PointType.END:
            return len(self.__points) + 1

        # Для промежуточных точек ищем позицию перед END
        end_point = next((p for p in self.__points if p.point_type == PointType.END), None)
        return end_point.order if end_point else len(self.__points)

    def add_point(self, qgs_point_xy: QgsPointXY, point_type: PointType, node_id: int):
        if not qgs_point_xy or not point_type or not node_id:
            raise BaseException("Для добавления требуются координаты, тип и ИД точки")

        order = self._insert_order(point_type)
        route_point = RoutePoint(
            id=self.__next_point_id,
            qgs_point_xy=qgs_point_xy,
            point_type=point_type,
            order=order,
            node_id=node_id,
        )

        self.__next_point_id += 1
        self.__points.append(route_point)

        self.__points.sort_by_order()
        self._reindex()

    def remove_point(self, point_id: int) -> RoutePoint | None:
        point = self.__points.remove_by_id(point_id)
        if point:
            self._reindex()
        return point

    def clear(self):
        self.__points.clear()
        self.__next_point_id = 1

    def __sort_key(self, p: RoutePoint):
        if p.point_type == PointType.START: return (0, p.order)
        if p.point_type == PointType.END: return (2, p.order)
        return (1, p.order)

    def change_point_type(self, point_id: int, new_type: PointType) -> RoutePoint | None:
        target_point = self.get_point(point_id)
        if not target_point:
            return None

        target_point.point_type = new_type
        sorted_points = sorted(list(self.__points), key=self.__sort_key)
        self.__points.clear()
        for p in sorted_points:
            self.__points.append(p)

        self._reindex()
        return target_point

    def has_required_points(self) -> bool:
        has_start = any(p.point_type == PointType.START for p in self.__points)
        has_end = any(p.point_type == PointType.END for p in self.__points)
        return has_start and has_end

    def get_point(self, point_id: int) -> RoutePoint | None:
        return next((p for p in self.__points if p.id == point_id), None)

    def __str__(self):
        res = "RoutePointCollection [\n"
        for p in self.__points:
            res += f"  {p},\n"
        return res + "]"