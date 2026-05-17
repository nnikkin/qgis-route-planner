from qgis_route_planner.exceptions import ProfileOperationError
from qgis_route_planner.vehicle.vehicle_profile import VehicleProfile
from qgis_route_planner.vehicle.vehicle_repository import VehicleProfileRepository
from qgis_route_planner.vehicle.vehicle_type import VehicleType


class VehicleService:
    def __init__(self, vehicle_repo: VehicleProfileRepository):
        self.__vehicle_repo: VehicleProfileRepository = vehicle_repo

    def create_profile(self, name: str, vtype: VehicleType, height: float, width: float, depth: float, weight: float) -> VehicleProfile:
        try:
            profile = VehicleProfile(
                name=name,
                type=vtype,
                height=height,
                width=width,
                depth=depth,
                weight=weight
            )
            return self.__vehicle_repo.add_profile(profile)
        except OSError as e:
            raise ProfileOperationError(
                f"Ошибка создания профиля: {str(e)}",
                operation="create_profile"
            ) from e

    def get_profiles(self) -> list[VehicleProfile]:
        try:
            return self.__vehicle_repo.get_all()
        except OSError as e:
            raise ProfileOperationError(
                f"Ошибка получения списка профилей: {str(e)}",
                operation="get_profiles"
            ) from e

    def get_profile_by_id(self, profile_id: int) -> VehicleProfile:
        try:
            return self.__vehicle_repo.get_by_id(profile_id)
        except OSError as e:
            raise ProfileOperationError(
                f"Ошибка получения профиля: {str(e)}",
                operation="get_profile_by_id"
            ) from e

    def update_profile(self, profile_id: int, profile: VehicleProfile) -> bool:
        try:
            self.__vehicle_repo.upd_profile(profile_id, profile)
            return True
        except OSError as e:
            raise ProfileOperationError(
                f"Ошибка обновления профиля: {str(e)}",
                operation="update_profile"
            ) from e

    def delete_profile(self, profile_id: int) -> bool:
        try:
            self.__vehicle_repo.del_profile(profile_id)
            return True
        except OSError as e:
            raise ProfileOperationError(
                f"Ошибка удаления профиля: {str(e)}",
                operation="delete_profile"
            ) from e
