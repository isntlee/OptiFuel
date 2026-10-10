from dataclasses import dataclass

from job_processor.data.job_store import JobStore
from job_processor.data.model_store import ModelStore
from job_processor.data.weather import WeatherClient
from job_processor.settings import ServiceConfig


@dataclass(frozen=True)
class Shared:
    """The parts create_app builds once and every job needs."""

    config: ServiceConfig
    job_store: JobStore
    model_store: ModelStore
    weather_client: WeatherClient
