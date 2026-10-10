from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from job_processor.errors import WeatherUnavailable
from job_processor.main import create_app
from job_processor.schemas.wind import Wind
from job_processor.settings import Settings

# One degree east along the equator at 30,000 ft and 240 km/h: 60.04 nautical miles.
# With no wind and the ABC stand-in model that is 2,779.9 lb of fuel.
TEST_ROUTE = [
    {"latitude": 0, "longitude": 0, "altitude": 30000, "speed": 240},
    {"latitude": 0, "longitude": 1, "altitude": 30000, "speed": 240},
]


def flight_plan(aircraft_type: str = "B777") -> dict[str, Any]:
    return {
        "flight_id": 1,
        "airline": "ABC",
        "aircraft_type": aircraft_type,
        "registration": "ABC-1",
        "route": TEST_ROUTE,
    }


class FailingWeather:
    """A weather client whose service is always down."""

    def get_wind(
        self, latitude: float, longitude: float, altitude_feet: float, time: datetime
    ) -> Wind:
        raise WeatherUnavailable("weather service is down")


def settings_for(tmp_path: Path) -> Settings:
    """An empty database per test, and no wind from the fake weather."""
    return Settings(
        database_url=f"sqlite:///{tmp_path}/jobs.db", fake_weather="no_wind"
    )


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(settings_for(tmp_path)))


def submit_and_fetch(client: TestClient, plan: dict[str, Any]) -> dict[str, Any]:
    """Submit a plan, check it was accepted, then fetch the job as airline ABC."""
    submitted = client.post("/v1/jobs", json=plan)
    assert submitted.status_code == 202
    job_id = submitted.json()["job_id"]
    fetched = client.get(f"/v1/jobs/{job_id}", headers={"X-Airline": "ABC"})
    assert fetched.status_code == 200
    job: dict[str, Any] = fetched.json()
    return job


def test_a_normal_flight_plan_gives_the_right_fuel_total(client: TestClient) -> None:
    job = submit_and_fetch(client, flight_plan())
    assert job["status"] == "completed"
    assert job["total_fuel_lb"] == pytest.approx(2779.9, abs=0.5)
    assert job["warnings"] == []


def test_a_job_is_not_visible_to_another_airline(client: TestClient) -> None:
    job_id = client.post("/v1/jobs", json=flight_plan()).json()["job_id"]
    fetched = client.get(f"/v1/jobs/{job_id}", headers={"X-Airline": "XYZ"})
    assert fetched.status_code == 404


def test_a_disabled_aircraft_type_is_rejected(client: TestClient) -> None:
    job = submit_and_fetch(client, flight_plan(aircraft_type="A380"))
    assert job["status"] == "rejected"
    assert "A380" in job["reason"]


def test_weather_failure_still_gives_a_result(tmp_path: Path) -> None:
    client = TestClient(
        create_app(settings_for(tmp_path), weather_client=FailingWeather())
    )
    job = submit_and_fetch(client, flight_plan())
    assert job["status"] == "completed"
    assert job["warnings"] == ["no weather available"]
    assert job["total_fuel_lb"] == pytest.approx(2779.9, abs=0.5)
