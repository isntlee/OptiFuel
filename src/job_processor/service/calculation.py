from itertools import pairwise

from job_processor.data.model_store import FuelModel
from job_processor.errors import Rejected
from job_processor.schemas.flight_plan import FlightPlan, RoutePoint
from job_processor.schemas.leg import Leg
from job_processor.schemas.result import FuelResult
from job_processor.schemas.wind import Wind
from job_processor.service.geometry import (
    distance_nautical_miles,
    headwind_knots,
    initial_bearing_degrees,
)
from job_processor.settings import SpeedUnit

KNOTS_PER_UNIT: dict[SpeedUnit, float] = {"km/h": 0.53996, "knots": 1.0, "m/s": 1.94384}


def calculate_fuel(
    flight_plan: FlightPlan, wind: Wind, model: FuelModel, speed_unit: SpeedUnit
) -> FuelResult:
    """Work out the fuel for the whole route. Makes no outside calls."""
    legs = build_legs(flight_plan.route, speed_unit)
    times_hours = apply_wind(legs, wind)
    fuel_flows = model.predict_fuel_flow(legs)
    return total(legs, times_hours, fuel_flows)


def build_legs(route: list[RoutePoint], speed_unit: SpeedUnit) -> list[Leg]:
    """One leg for each pair of neighbouring route points."""
    return [build_leg(start, end, speed_unit) for start, end in pairwise(route)]


def build_leg(start: RoutePoint, end: RoutePoint, speed_unit: SpeedUnit) -> Leg:
    """A leg takes the average of its two end points."""
    return Leg(
        airspeed_knots=(start.speed + end.speed) / 2 * KNOTS_PER_UNIT[speed_unit],
        altitude_feet=(start.altitude + end.altitude) / 2,
        distance_nautical_miles=distance_nautical_miles(start, end),
        bearing_degrees=initial_bearing_degrees(start, end),
    )


def apply_wind(legs: list[Leg], wind: Wind) -> list[float]:
    """Time in hours for each leg, once the wind has changed its ground speed."""
    times_hours = []
    for leg in legs:
        headwind = headwind_knots(
            wind.speed_knots, wind.direction_degrees, leg.bearing_degrees
        )
        ground_speed_knots = leg.airspeed_knots - headwind
        if ground_speed_knots <= 0:
            raise Rejected("ground speed not positive")
        times_hours.append(leg.distance_nautical_miles / ground_speed_knots)
    return times_hours


def total(
    legs: list[Leg], times_hours: list[float], fuel_flows: list[float]
) -> FuelResult:
    """Add up fuel, distance, and time over the legs."""
    return FuelResult(
        total_fuel_lb=sum(
            flow * time for flow, time in zip(fuel_flows, times_hours, strict=True)
        ),
        total_distance_nm=sum(leg.distance_nautical_miles for leg in legs),
        total_time_hours=sum(times_hours),
    )
