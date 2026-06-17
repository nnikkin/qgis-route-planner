from __future__ import annotations

import json
from pathlib import Path

from qgis_route_planner.vehicle import VehicleType
from qgis_route_planner.vehicle.vehicle_profile import VehicleProfile


class VehicleProfileRepository:
    def __init__(self):
        self.__storage_file = "vehicle_profiles.json"
        self.__storage_path = (Path(__file__).parent / self.__storage_file).resolve()

    def get_all(self) -> list[VehicleProfile]:
        return [self.__dict_to_profile(item) for item in self.__load_profiles()]

    def get_by_id(self, profile_id: int) -> VehicleProfile | None:
        for profile in self.get_all():
            if profile.id == profile_id:
                return profile
        return None

    def add_profile(self, profile: VehicleProfile) -> VehicleProfile:
        profiles = self.__load_profiles()
        next_id = self.__get_next_id(profiles)
        profile.id = next_id
        profiles.append(self.__profile_to_dict(profile))
        self.__save_profiles(profiles)
        return profile

    def del_profile(self, profile_id: int):
        profiles = [item for item in self.__load_profiles() if item.get("id") != profile_id]
        self.__save_profiles(profiles)

    def upd_profile(self, profile_id: int, profile: VehicleProfile):
        profiles = self.__load_profiles()
        profile.id = profile_id
        for index, item in enumerate(profiles):
            if item.get("id") == profile_id:
                profiles[index] = self.__profile_to_dict(profile)
                self.__save_profiles(profiles)
                return
        profiles.append(self.__profile_to_dict(profile))
        self.__save_profiles(profiles)

    def __load_profiles(self) -> list[dict]:
        try:
            with open(self.__storage_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            return []
        return data if isinstance(data, list) else []

    def __save_profiles(self, profiles: list[dict]):
        with open(self.__storage_path, "w", encoding="utf-8") as file:
            json.dump(profiles, file, ensure_ascii=False, indent=2)

    def __get_next_id(self, profiles: list[dict]) -> int:
        ids = [int(item.get("id") or 0) for item in profiles]
        return max(ids, default=0) + 1

    @staticmethod
    def __dict_to_profile(data: dict) -> VehicleProfile:
        return VehicleProfile(
            id=data.get("id"),
            name=data.get("name", ""),
            type=data.get("type", VehicleType.CAR),
            height_m=float(data.get("height_m") or 0.01),
            width_m=float(data.get("width_m") or 0.01),
            weight_t=float(data.get("weight_t") or 0.01),
            depth_m=float(data.get("depth_m") or 0.01),
        )

    @staticmethod
    def __profile_to_dict(profile: VehicleProfile) -> dict:
        return {
            "id": profile.id,
            "name": profile.name,
            "type": profile.type.name,
            "height_m": profile.height_m,
            "width_m": profile.width_m,
            "weight_t": profile.weight_t,
            "depth_m": profile.depth_m
        }