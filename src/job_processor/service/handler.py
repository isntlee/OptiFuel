import logging

from job_processor.data.job_store import JobStore
from job_processor.data.model_store import ModelStore
from job_processor.data.weather import WeatherClient
from job_processor.errors import Rejected
from job_processor.schemas.flight_plan import FlightPlan
from job_processor.schemas.job import JobOutcome
from job_processor.service.pipeline import run_pipeline
from job_processor.settings import ServiceConfig

logger = logging.getLogger(__name__)


def handle_message(
    job_id: str,
    flight_plan: FlightPlan,
    job_store: JobStore,
    config: ServiceConfig,
    weather_client: WeatherClient,
    model_store: ModelStore,
) -> None:
    """Process one job. This is what a queue consumer would call in production."""
    job = job_store.get_job(job_id)
    if job is None:
        logger.error("Job %s not found", job_id)
        return
    # The same message delivered twice does the work once.
    if job.status != "pending":
        logger.info("Job %s is already %s", job_id, job.status)
        return
    try:
        outcome = run_pipeline(flight_plan, config, weather_client, model_store)
    except Rejected as error:
        outcome = JobOutcome(status="rejected", reason=str(error))
    except Exception as error:
        logger.exception("Job %s failed", job_id)
        outcome = JobOutcome(status="failed", reason=str(error))
    if not job_store.save_outcome(job_id, outcome):
        logger.info("Job %s was already saved by another worker", job_id)
