from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import JSON, DateTime, create_engine, make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class JobRow(Base):
    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(primary_key=True)
    airline: Mapped[str]
    flight_id: Mapped[int]
    aircraft_type: Mapped[str]
    registration: Mapped[str]
    flight_plan: Mapped[dict[str, Any]] = mapped_column(JSON)
    status: Mapped[str]
    reason: Mapped[str | None]
    total_fuel_lb: Mapped[float | None]
    total_distance_nm: Mapped[float | None]
    total_time_hours: Mapped[float | None]
    warnings: Mapped[list[str]] = mapped_column(JSON)
    model_id: Mapped[str | None]
    model_version: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)


def make_session_factory(database_url: str) -> sessionmaker[Session]:
    """Connect, create the jobs table if it is missing, and return a session opener."""
    connect_args = {}
    url = make_url(database_url)
    if url.drivername == "sqlite" and url.database:
        # SQLite creates the file but not the folder it sits in.
        Path(url.database).parent.mkdir(parents=True, exist_ok=True)
        # Background work runs on thread-pool threads, which SQLite refuses by default.
        connect_args = {"check_same_thread": False}
    engine = create_engine(database_url, connect_args=connect_args)
    Base.metadata.create_all(engine)
    return sessionmaker(engine)
