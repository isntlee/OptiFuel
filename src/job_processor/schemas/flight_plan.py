from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class RoutePoint(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    altitude: float = Field(ge=0)  # feet
    speed: float = Field(gt=0)  # unit set by speed_unit in the settings file


class FlightPlan(BaseModel):
    """A flight to estimate fuel for. Fields not listed here are ignored."""

    flight_id: int
    airline: NonEmptyText
    aircraft_type: NonEmptyText
    registration: NonEmptyText
    route: list[RoutePoint] = Field(min_length=2)
