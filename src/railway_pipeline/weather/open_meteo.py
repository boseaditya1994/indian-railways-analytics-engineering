"""Small Open-Meteo historical client with explicit, bounded requests."""

from __future__ import annotations

from datetime import date
from typing import Any

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class WeatherSourceError(RuntimeError):
    """Raised when the weather service cannot provide an approved response."""


class OpenMeteoHistoricalClient:
    base_url = "https://archive-api.open-meteo.com/v1/archive"

    def __init__(self, session: requests.Session | None = None, timeout_seconds: float = 20.0) -> None:
        self.session = session or requests.Session()
        self.timeout_seconds = timeout_seconds

    @retry(
        retry=retry_if_exception_type(requests.RequestException),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def daily_weather(self, latitude: float, longitude: float, observed_date: date) -> dict[str, Any]:
        response = self.session.get(
            self.base_url,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "start_date": observed_date.isoformat(),
                "end_date": observed_date.isoformat(),
                "daily": "temperature_2m_mean,precipitation_sum,rain_sum,weather_code",
                "timezone": "Asia/Kolkata",
            },
            timeout=self.timeout_seconds,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            raise WeatherSourceError(f"Open-Meteo returned HTTP {response.status_code}") from error
        payload: dict[str, Any] = response.json()
        if "daily" not in payload:
            raise WeatherSourceError("Open-Meteo response lacks daily weather data")
        return payload
