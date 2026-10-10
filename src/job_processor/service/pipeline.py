from job_processor.errors import Rejected
from job_processor.schemas.flight_plan import FlightPlan
from job_processor.settings import ServiceConfig


def check_allowed(flight_plan: FlightPlan, config: ServiceConfig) -> None:
    """Reject a plan whose aircraft type is disabled or whose airline has no model."""
    if flight_plan.aircraft_type not in config.enabled_aircraft_types:
        raise Rejected(f"aircraft type {flight_plan.aircraft_type} is not enabled")
    if flight_plan.airline not in config.airlines:
        raise Rejected(f"no model configured for airline {flight_plan.airline}")
