from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

ShortText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)
]

# Upper limits are sanity checks: no aircraft flies above them in any supported unit.
# Infinity and NaN are refused because they pass through the maths as "completed".


class RoutePoint(BaseModel):
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    altitude: float = Field(ge=0, le=100_000, allow_inf_nan=False)  # feet
    speed: float = Field(gt=0, le=2_000, allow_inf_nan=False)  # unit from settings


class FlightPlan(BaseModel):
    """A flight to estimate fuel for. Fields not listed here are ignored."""

    flight_id: int = Field(ge=0, lt=2**63)  # must fit a database integer
    airline: ShortText
    aircraft_type: ShortText
    registration: ShortText
    route: list[RoutePoint] = Field(min_length=2, max_length=10_000)
