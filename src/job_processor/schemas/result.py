from pydantic import BaseModel


class FuelResult(BaseModel):
    total_fuel_lb: float
    total_distance_nm: float
    total_time_hours: float
