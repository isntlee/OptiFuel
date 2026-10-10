from datetime import datetime
from typing import Protocol

import httpx
from pydantic import BaseModel

from job_processor.errors import WeatherUnavailable
from job_processor.schemas.wind import Wind
from job_processor.settings import FakeWeather


class WeatherClient(Protocol):
    def get_wind(
        self, latitude: float, longitude: float, altitude_feet: float, time: datetime
    ) -> Wind:
        """The wind at one place and time. Raises WeatherUnavailable on any failure."""
        ...


FAKE_WINDS: dict[FakeWeather, Wind] = {
    "no_wind": Wind(speed_knots=0, direction_degrees=0),
    "calm": Wind(speed_knots=10, direction_degrees=90),
    "strong": Wind(speed_knots=40, direction_degrees=90),
}


class FakeWeatherClient:
    """Returns one fixed wind, chosen by the FAKE_WEATHER setting."""

    def __init__(self, setting: FakeWeather) -> None:
        self.wind = FAKE_WINDS[setting]

    def get_wind(
        self, latitude: float, longitude: float, altitude_feet: float, time: datetime
    ) -> Wind:
        """The wind at one place and time. Raises WeatherUnavailable on any failure."""
        return self.wind


class WindReply(BaseModel):
    """What the assumed weather service sends back."""

    wind_speed: float  # knots
    wind_direction: float  # degrees, where the wind blows from


class HttpWeatherClient:
    """Calls GET {base_url}/wind with a bearer token. No retries."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout_seconds: float,
        transport: httpx.BaseTransport | None = None,  # tests pass a fake transport
    ) -> None:
        self.client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout_seconds,
            transport=transport,
        )

    def get_wind(
        self, latitude: float, longitude: float, altitude_feet: float, time: datetime
    ) -> Wind:
        """The wind at one place and time. Raises WeatherUnavailable on any failure."""
        params: dict[str, float | str] = {
            "latitude": latitude,
            "longitude": longitude,
            "altitude": altitude_feet,
            "time": time.isoformat(),
        }
        try:
            response = self.client.get("/wind", params=params)
            response.raise_for_status()
            reply = WindReply.model_validate(response.json())
        # httpx.HTTPError covers timeouts, connection errors, and non-200 replies.
        # ValueError covers a body that is not JSON or not the expected shape.
        except (httpx.HTTPError, ValueError) as error:
            raise WeatherUnavailable(str(error)) from error
        return Wind(
            speed_knots=reply.wind_speed, direction_degrees=reply.wind_direction
        )
