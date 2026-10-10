from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from job_processor.schemas.result import FuelResult

JobStatus = Literal["pending", "completed", "rejected", "failed"]


class Job(BaseModel):
    """What a client gets back. The flight plan is stored but not returned."""

    job_id: str
    status: JobStatus
    airline: str
    flight_id: int
    aircraft_type: str
    registration: str
    total_fuel_lb: float | None
    total_distance_nm: float | None
    total_time_hours: float | None
    warnings: list[str]
    reason: str | None
    model_id: str | None
    model_version: str | None
    created_at: datetime
    completed_at: datetime | None


class JobOutcome(BaseModel):
    status: Literal["completed", "rejected", "failed"]
    reason: str | None = None
    result: FuelResult | None = None
    warnings: list[str] = []
    model_id: str | None = None
    model_version: str | None = None
