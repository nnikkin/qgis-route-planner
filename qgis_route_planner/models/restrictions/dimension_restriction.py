from qgis_route_planner.models.restrictions.base_restriction import BaseRestriction


class DimensionRestriction(BaseRestriction):
    def __init__(self, node_ids: list[int], name: str, comment: str, height: float, width: float, weight: float):
        super().__init__(node_ids, name, comment)
        self.__weight = weight
        self.__height = height
        self.__width = width

    @property
    def weight(self) -> float:
        return self.__weight

    @property
    def height(self) -> float:
        return self.__height

    @property
    def width(self) -> float:
        return self.__width