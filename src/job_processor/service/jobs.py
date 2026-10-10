import uuid

from job_processor.data.job_store import JobStore
from job_processor.schemas.flight_plan import FlightPlan
from job_processor.schemas.job import Job


def submit_job(job_store: JobStore, flight_plan: FlightPlan) -> str:
    """Save the plan as a pending job and return its new job ID."""
    job_id = str(uuid.uuid4())
    job_store.create_job(job_id, flight_plan)
    return job_id


def get_job(job_store: JobStore, job_id: str, airline: str) -> Job | None:
    """Read a job, only if it belongs to the airline asking."""
    return job_store.get_job_for_airline(job_id, airline)
