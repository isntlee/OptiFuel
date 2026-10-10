import logging
from datetime import UTC, datetime

from job_processor.data.model_store import ModelStore
from job_processor.data.weather import WeatherClient
from job_processor.errors import Rejected, WeatherUnavailable
from job_processor.schemas.flight_plan import FlightPlan
from job_processor.schemas.job import JobOutcome
from job_processor.schemas.wind import NO_WIND, Wind
from job_processor.service.calculation import calculate_fuel
from job_processor.settings import ServiceConfig

logger = logging.getLogger(__name__)


def run_pipeline(
    flight_plan: FlightPlan,
    config: ServiceConfig,
    weather_client: WeatherClient,
    model_store: ModelStore,
) -> JobOutcome:
    """The four steps for one job. Raises Rejected; any other error means failed."""
    check_allowed(flight_plan, config)
    wind, warnings = get_wind(flight_plan, weather_client)
    model = model_store.get(flight_plan.airline)
    result = calculate_fuel(flight_plan, wind, model, config.speed_unit)
    return JobOutcome(
        status="completed",
        result=result,
        warnings=warnings,
        model_id=model.model_id,
        model_version=model.version,
    )


def check_allowed(flight_plan: FlightPlan, config: ServiceConfig) -> None:
    """Reject a plan whose aircraft type is disabled or whose airline has no model."""
    if flight_plan.aircraft_type not in config.enabled_aircraft_types:
        raise Rejected(f"aircraft type {flight_plan.aircraft_type} is not enabled")
    if flight_plan.airline not in config.airlines:
        raise Rejected(f"no model configured for airline {flight_plan.airline}")


def get_wind(
    flight_plan: FlightPlan, weather_client: WeatherClient
) -> tuple[Wind, list[str]]:
    """One weather call, for the first route point and the current time.

    If it fails the job goes on with no wind and a warning, never a rejection.
    """
    first = flight_plan.route[0]
    try:
        wind = weather_client.get_wind(
            first.latitude, first.longitude, first.altitude, datetime.now(UTC)
        )
    except WeatherUnavailable as error:
        logger.warning("Weather unavailable: %s", error)
        return NO_WIND, ["no weather available"]
    return wind, []
