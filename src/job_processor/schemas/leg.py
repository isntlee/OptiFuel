from pydantic import BaseModel


class Leg(BaseModel):
    airspeed_knots: float
    altitude_feet: float
    distance_nautical_miles: float
    bearing_degrees: float
