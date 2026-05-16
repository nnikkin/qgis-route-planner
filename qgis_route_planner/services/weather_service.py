from __future__ import annotations
from typing import Any

import requests


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
            print(f"HTTP ошибка: {http_err}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Ошибка соединения с сервисом погоды: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            print(f"Истекло время ожидания сервиса погоды: {timeout_err}")
        except Exception as err:
            print(f"Произошла ошибка во время получения данных из сервиса погоды: {err}")
        return None

    def calculate_weather(self) -> dict | None:
        """ Получить погодные данные для текущих координат сервиса. """
        return self.get_weather_data()

    def test_connection(
            self,
            lon: float | str = "37.6173",
            lat: float | str = "55.7558",
    ) -> bool:
        """ Проверить доступность сервиса и корректность API-ключа. """
        return self.get_weather_data(lon=lon, lat=lat) is not None


if __name__ == "__main__":
    w = WeatherService()
    print(w.get_weather_data(lat="59.13", lon="39.54", key="973e67cbeadac6d9942d3282f8ac96a2"))
