from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from job_processor.data.job_store import JobStore
from job_processor.data.jobs_table import make_session_factory
from job_processor.schemas.flight_plan import FlightPlan, RoutePoint
from job_processor.schemas.job import JobOutcome


def test_only_one_of_many_workers_can_save_an_outcome(tmp_path: Path) -> None:
    store = JobStore(make_session_factory(f"sqlite:///{tmp_path}/jobs.db"))
    start = RoutePoint(latitude=0, longitude=0, altitude=30000, speed=240)
    end = RoutePoint(latitude=0, longitude=1, altitude=30000, speed=240)
    plan = FlightPlan(
        flight_id=1,
        airline="ABC",
        aircraft_type="B777",
        registration="X",
        route=[start, end],
    )
    store.create_job("job-1", plan)

    # Eight workers race to save an outcome for the same job. The database decides who wins.
    outcomes = [JobOutcome(status="failed", reason=f"worker {i}") for i in range(8)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(
            pool.map(lambda outcome: store.save_outcome("job-1", outcome), outcomes)
        )

    assert results.count(True) == 1
    job = store.get_job("job-1")
    assert job is not None
    assert job.status == "failed"
