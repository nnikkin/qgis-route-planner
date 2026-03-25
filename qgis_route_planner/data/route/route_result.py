from . import RouteEdge
from ...utils import DoublyLinkedList


class RouteResult:
    """ Результат расчёта маршрута """
    def __init__(self):
        self.__edges: DoublyLinkedList = DoublyLinkedList()
        self.__next_edge_id = 1

    @property
    def edges(self) -> DoublyLinkedList:
        return self.__edges

    @property
    def next_edge_id(self) -> int:
        return self.__next_edge_id

    def get_edge_ids(self) -> list[int]:
        return [e.edge_id for e in self.__edges]

    def add_edge(self):
        pass

    def remove_edge(self):
        pass

    def clear(self):
        self.__edges.clear()
        self.__next_edge_id = 1

    def get_edge(self, edge_id: int) -> RouteEdge | None:
        return next((e for e in self.__edges if e.id == edge_id), None)

    def __str__(self):
        res = "RouteResult [\n"
        for e in self.__edges:
            res += f"  {e},\n"
        return res + "]"