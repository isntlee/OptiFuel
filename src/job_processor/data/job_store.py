from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session, sessionmaker

from job_processor.data.jobs_table import JobRow
from job_processor.schemas.flight_plan import FlightPlan
from job_processor.schemas.job import Job, JobOutcome


class JobStore:
    """The only code that touches the database. Every call opens its own short session."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def create_job(self, job_id: str, flight_plan: FlightPlan) -> None:
        """Save a new job as pending."""
        row = JobRow(
            job_id=job_id,
            airline=flight_plan.airline,
            flight_id=flight_plan.flight_id,
            aircraft_type=flight_plan.aircraft_type,
            registration=flight_plan.registration,
            flight_plan=flight_plan.model_dump(),
            status="pending",
            warnings=[],
            created_at=datetime.now(UTC),
        )
        with self.session_factory.begin() as session:
            session.add(row)

    def get_job(self, job_id: str) -> Job | None:
        """Read a job by its ID. Used by the handler."""
        with self.session_factory() as session:
            row = session.get(JobRow, job_id)
            return to_job(row) if row else None

    def get_job_for_airline(self, job_id: str, airline: str) -> Job | None:
        """Read a job by its ID, only if it belongs to the airline. Used by the fetch route."""
        statement = select(JobRow).where(
            JobRow.job_id == job_id, JobRow.airline == airline
        )
        with self.session_factory() as session:
            row = session.scalar(statement)
            return to_job(row) if row else None

    def save_outcome(self, job_id: str, outcome: JobOutcome) -> bool:
        """Write the outcome only if the job is still pending. False means another worker won."""
        result = outcome.result
        statement = (
            update(JobRow)
            .where(JobRow.job_id == job_id, JobRow.status == "pending")
            .values(
                status=outcome.status,
                reason=outcome.reason,
                total_fuel_lb=result.total_fuel_lb if result else None,
                total_distance_nm=result.total_distance_nm if result else None,
                total_time_hours=result.total_time_hours if result else None,
                warnings=outcome.warnings,
                model_id=outcome.model_id,
                model_version=outcome.model_version,
                completed_at=datetime.now(UTC),
            )
        )
        with self.session_factory.begin() as session:
            return session.connection().execute(statement).rowcount == 1


def to_job(row: JobRow) -> Job:
    """Turn a table row into plain data, so the table class never leaves this layer."""
    job = Job.model_validate(row, from_attributes=True)
    return job.model_copy(
        update={
            "created_at": as_utc(job.created_at),
            "completed_at": as_utc(job.completed_at) if job.completed_at else None,
        }
    )


def as_utc(time: datetime) -> datetime:
    """Times are stored as UTC, but SQLite hands them back without a timezone."""
    return time.replace(tzinfo=UTC) if time.tzinfo is None else time.astimezone(UTC)
