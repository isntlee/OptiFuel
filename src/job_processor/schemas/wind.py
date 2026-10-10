from pydantic import BaseModel


class Wind(BaseModel):
    speed_knots: float
    direction_degrees: float  # where the wind blows from, 0 is north


NO_WIND = Wind(speed_knots=0, direction_degrees=0)
