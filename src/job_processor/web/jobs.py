from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request

from job_processor.schemas.flight_plan import FlightPlan
from job_processor.schemas.job import Job, JobAccepted
from job_processor.service.handler import handle_message
from job_processor.service.jobs import get_job, submit_job
from job_processor.service.shared import Shared

router = APIRouter(prefix="/v1/jobs")


@router.post("", status_code=202)
def submit(
    flight_plan: FlightPlan, request: Request, background_tasks: BackgroundTasks
) -> JobAccepted:
    """Accept a flight plan, reply with a job ID, then process it after replying."""
    shared: Shared = request.app.state.shared
    job_id = submit_job(shared.job_store, flight_plan)
    # In production a queue sits here. The background task stands in for it.
    background_tasks.add_task(handle_message, job_id, flight_plan, shared)
    return JobAccepted(job_id=job_id)


@router.get("/{job_id}")
def fetch(job_id: str, request: Request, x_airline: Annotated[str, Header()]) -> Job:
    """Return the job, only to the airline it belongs to. Otherwise 404."""
    shared: Shared = request.app.state.shared
    job = get_job(shared.job_store, job_id, x_airline)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job
