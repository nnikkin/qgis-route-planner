from . import BaseRestriction


class TemporaryRestriction(BaseRestriction):
    def __init__(self, node_ids: list[int], name: str, comment: str,
                 valid_from_date: str, valid_from_time: str, valid_to_date: str, valid_to_time: str):
        super().__init__(node_ids, name, comment)
        self.__valid_from_date = valid_from_date
        self.__valid_from_time = valid_from_time
        self.__valid_to_date = valid_to_date
        self.__valid_to_time = valid_to_time

    @property
    def valid_from_date(self) -> str:
        return self.__valid_from_date

    @property
    def valid_from_time(self) -> str:
        return self.__valid_from_time

    @property
    def valid_to_date(self) -> str:
        return self.__valid_to_date

    @property
    def valid_to_time(self) -> str:
        return self.__valid_to_time