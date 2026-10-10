from pydantic import BaseModel, Field


class RoutePoint(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    altitude: float = Field(ge=0)  # feet
    speed: float = Field(gt=0)  # unit set by speed_unit in the settings file


class FlightPlan(BaseModel):
    """A flight to estimate fuel for. Fields not listed here are ignored."""

    flight_id: int
    airline: str = Field(min_length=1)
    aircraft_type: str = Field(min_length=1)
    registration: str = Field(min_length=1)
    route: list[RoutePoint] = Field(min_length=2)
