from datetime import date

import pytest

from railway_pipeline.weather.open_meteo import OpenMeteoHistoricalClient, WeatherSourceError


class Response:
    status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return {"daily": {"time": ["2024-01-01"], "rain_sum": [0.0]}}


class Session:
    def __init__(self, response: Response) -> None:
        self.response = response
        self.parameters: dict[str, object] = {}

    def get(self, url: str, **kwargs: object) -> Response:
        self.parameters = {"url": url, **kwargs}
        return self.response


def test_weather_client_requests_single_day_with_bounded_timeout() -> None:
    session = Session(Response())
    result = OpenMeteoHistoricalClient(session=session).daily_weather(22.57, 88.36, date(2024, 1, 1))
    assert result["daily"]["rain_sum"] == [0.0]
    assert session.parameters["timeout"] == 20.0


def test_weather_client_rejects_missing_daily_data() -> None:
    class EmptyResponse(Response):
        def json(self) -> dict[str, object]:
            return {}

    with pytest.raises(WeatherSourceError, match="lacks daily"):
        OpenMeteoHistoricalClient(session=Session(EmptyResponse())).daily_weather(22.57, 88.36, date(2024, 1, 1))
