from typing import Protocol


class WeatherSettingsProvider(Protocol):
    def test_connection(self):
        pass