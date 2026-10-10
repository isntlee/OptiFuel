import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings

SpeedUnit = Literal["km/h", "knots", "m/s"]


class AirlineConfig(BaseModel):
    model_path: Path


class ServiceConfig(BaseModel):
    """The contents of config/service.toml."""

    speed_unit: SpeedUnit
    enabled_aircraft_types: list[str]
    airlines: dict[str, AirlineConfig]


def load_service_config(path: Path) -> ServiceConfig:
    """Read the settings file and check its shape."""
    with path.open("rb") as file:
        return ServiceConfig.model_validate(tomllib.load(file))


class Settings(BaseSettings):
    """Values read from environment variables, with defaults for local use."""

    config_path: Path = Path("config/service.toml")
    database_url: str = "sqlite:///storage/jobs.db"
    weather_provider: Literal["fake", "http"] = "fake"
    weather_api_url: str | None = None
    weather_api_key: str | None = None
    weather_timeout_seconds: float = 2.0
    fake_weather: Literal["no_wind", "calm", "strong"] = "no_wind"
    log_level: str = "INFO"
