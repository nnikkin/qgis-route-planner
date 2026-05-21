from typing import Protocol


class WeatherSettingsProvider(Protocol):
    def test_connection(self, api_url: str | None = None, api_key: str | None = None):
        pass
