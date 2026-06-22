from __future__ import annotations
from typing import Any

import requests

from qgis_route_planner.exceptions import WeatherServiceError


class WeatherService:
    def __init__(self, api_key: str = "", api_url: str | None = None):
        self.__api_url = api_url or "https://api.openweathermap.org/data/2.5/weather"
        self.__api_key = api_key
        self.__lon: float | None = None
        self.__lat: float | None = None

    def set_api_url(self, api_url: str):
        self.__api_url = api_url or "https://api.openweathermap.org/data/2.5/weather"

    def set_api_key(self, api_key: str):
        self.__api_key = api_key or ""

    def has_api_key(self) -> bool:
        return bool(self.__api_key)

    def set_location(self, lon: float, lat: float):
        self.__lon = lon
        self.__lat = lat

    def get_weather_data(
            self,
            lon: float | str | None = None,
            lat: float | str | None = None,
            key: str | None = None,
            city_id=None,
    ) -> Any | None:
        lon = lon if lon is not None else self.__lon
        lat = lat if lat is not None else self.__lat
        api_key = key if key is not None else self.__api_key
        if lon is None or lat is None or not api_key:
            return None

        payload = {
            "lat": lat,
            "lon": lon,
            "appid": api_key,
            "units": "metric",
            "lang": "ru"
        }
        if city_id is not None:
            payload["id"] = city_id

        try:
            response = requests.get(self.__api_url, params=payload, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            raise WeatherServiceError(f"Ошибка: {http_err}") from http_err
        except requests.exceptions.ConnectionError as conn_err:
            raise WeatherServiceError("Не удалось подключиться к сервису погоды.") from conn_err
        except requests.exceptions.Timeout as timeout_err:
            raise WeatherServiceError("Истекло время ожидания сервиса погоды.") from timeout_err
        except Exception as err:
            raise WeatherServiceError(f"Произошла ошибка во время получения данных из сервиса погоды: {err}") from err

    def calculate_weather(self) -> dict | None:
        """ Получить погодные данные для текущих координат сервиса. """
        return self.get_weather_data()

    def get_season_factor(
            self,
            summer_factor: float,
            winter_factor: float,
            fallback: str = "summer",
            data: dict | None = None,
    ) -> float:
        data = data if data is not None else self.get_weather_data()
        if data is None:
            return summer_factor if fallback == "summer" else winter_factor

        temp = data.get("main", {}).get("temp")
        weather_ids = [w.get("id", 0) for w in data.get("weather", [])]

        is_winter_conditions = (
                (temp is not None and temp < 2)
                or any(200 <= wid < 700 and wid not in range(500, 505) for wid in weather_ids)
                or any(600 <= wid < 700 for wid in weather_ids)
        )

        return winter_factor if is_winter_conditions else summer_factor

    def test_connection(
            self,
            api_url: str | None = None,
            api_key: str | None = None,
            lon: float | str = "37.6173",
            lat: float | str = "55.7558",
    ) -> bool:
        """ Проверить доступность сервиса и корректность API-ключа. """
        old_api_url = self.__api_url
        old_api_key = self.__api_key
        try:
            if api_url:
                self.set_api_url(api_url)
            if api_key is not None:
                self.set_api_key(api_key)
            return self.get_weather_data(lon=lon, lat=lat) is not None
        finally:
            self.__api_url = old_api_url
            self.__api_key = old_api_key
