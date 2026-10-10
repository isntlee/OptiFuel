import math

from job_processor.schemas.flight_plan import RoutePoint

EARTH_RADIUS_NAUTICAL_MILES = 3440.065


def distance_nautical_miles(start: RoutePoint, end: RoutePoint) -> float:
    """Great-circle distance between two points, by the haversine formula."""
    latitude_1 = math.radians(start.latitude)
    latitude_2 = math.radians(end.latitude)
    delta_latitude = latitude_2 - latitude_1
    delta_longitude = math.radians(end.longitude - start.longitude)
    half_chord = (
        math.sin(delta_latitude / 2) ** 2
        + math.cos(latitude_1)
        * math.cos(latitude_2)
        * math.sin(delta_longitude / 2) ** 2
    )
    angle = 2 * math.atan2(math.sqrt(half_chord), math.sqrt(1 - half_chord))
    return EARTH_RADIUS_NAUTICAL_MILES * angle


def initial_bearing_degrees(start: RoutePoint, end: RoutePoint) -> float:
    """Direction from start to end in degrees, 0 to 360, where 0 is north."""
    latitude_1 = math.radians(start.latitude)
    latitude_2 = math.radians(end.latitude)
    delta_longitude = math.radians(end.longitude - start.longitude)
    x = math.sin(delta_longitude) * math.cos(latitude_2)
    y = math.cos(latitude_1) * math.sin(latitude_2) - math.sin(latitude_1) * math.cos(
        latitude_2
    ) * math.cos(delta_longitude)
    return math.degrees(math.atan2(x, y)) % 360


def headwind_knots(
    wind_speed_knots: float, wind_direction_degrees: float, bearing_degrees: float
) -> float:
    """The part of the wind blowing against the direction of travel. Negative is a tailwind."""
    return wind_speed_knots * math.cos(
        math.radians(wind_direction_degrees - bearing_degrees)
    )
