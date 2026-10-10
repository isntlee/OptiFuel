import logging
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel

from job_processor.schemas.leg import Leg

logger = logging.getLogger(__name__)


class ModelFile(BaseModel):
    """The JSON a model file holds: parameters only, never code."""

    model_id: str
    version: str
    airline: str
    type: Literal["constant"]
    fuel_flow_lb_per_hour: float


class FuelModel(Protocol):
    model_id: str
    version: str

    def predict_fuel_flow(self, legs: list[Leg]) -> list[float]:
        """Fuel flow for each leg, in pounds per hour."""
        ...


class ConstantModel:
    """Stand-in: the same fuel flow whatever the speed and altitude."""

    def __init__(self, file: ModelFile) -> None:
        self.model_id = file.model_id
        self.version = file.version
        self.fuel_flow_lb_per_hour = file.fuel_flow_lb_per_hour

    def predict_fuel_flow(self, legs: list[Leg]) -> list[float]:
        """Fuel flow for each leg, in pounds per hour."""
        return [self.fuel_flow_lb_per_hour for _ in legs]


class ModelStore:
    def __init__(self, model_paths: dict[str, Path]) -> None:
        self.model_paths = model_paths
        self.loaded: dict[str, FuelModel] = {}

    def get(self, airline: str) -> FuelModel:
        """Return the airline's model, reading its file only on first use."""
        if airline not in self.loaded:
            self.loaded[airline] = self._load(airline)
        return self.loaded[airline]

    def _load(self, airline: str) -> FuelModel:
        path = self.model_paths[airline]
        file = ModelFile.model_validate_json(path.read_text())
        # One airline must never be served another airline's model.
        if file.airline != airline:
            raise ValueError(
                f"model file {path} belongs to {file.airline}, not {airline}"
            )
        logger.info(
            "Loaded model %s version %s for %s", file.model_id, file.version, airline
        )
        return ConstantModel(file)
