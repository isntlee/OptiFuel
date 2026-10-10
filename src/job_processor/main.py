import logging

from fastapi import FastAPI

from job_processor.data.job_store import JobStore
from job_processor.data.jobs_table import make_session_factory
from job_processor.data.model_store import ModelStore
from job_processor.data.weather import (
    FakeWeatherClient,
    HttpWeatherClient,
    WeatherClient,
)
from job_processor.service.shared import Shared
from job_processor.settings import Settings, load_service_config
from job_processor.web import health, jobs


def create_app(
    settings: Settings | None = None, weather_client: WeatherClient | None = None
) -> FastAPI:
    """Build the app and the shared parts the layers need. Tests pass their own weather client."""
    settings = settings or Settings()
    logging.basicConfig(level=settings.log_level)
    config = load_service_config(settings.config_path)

    shared = Shared(
        config=config,
        job_store=JobStore(make_session_factory(settings.database_url)),
        model_store=ModelStore(
            {name: airline.model_path for name, airline in config.airlines.items()}
        ),
        weather_client=weather_client or make_weather_client(settings),
    )
    app = FastAPI(title="OptiFuel job processor")
    app.state.shared = shared
    app.include_router(health.router)
    app.include_router(jobs.router)
    return app


def make_weather_client(settings: Settings) -> WeatherClient:
    """The fake client unless WEATHER_PROVIDER says http."""
    if settings.weather_provider == "fake":
        return FakeWeatherClient(settings.fake_weather)
    if not settings.weather_api_url or not settings.weather_api_key:
        raise ValueError(
            "WEATHER_API_URL and WEATHER_API_KEY are required for the http provider"
        )
    return HttpWeatherClient(
        settings.weather_api_url,
        settings.weather_api_key,
        settings.weather_timeout_seconds,
    )
