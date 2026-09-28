"""Chronological holdout splitting and model-comparison contracts."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import TypeVar

from railway_pipeline.prediction.metrics import mean_absolute_error, root_mean_squared_error

T = TypeVar("T")


@dataclass(frozen=True)
class EvaluationSummary:
    model_name: str
    row_count: int
    mae: float
    rmse: float
    baseline_mae: float

    @property
    def improves_on_baseline(self) -> bool:
        return self.mae < self.baseline_mae


def chronological_split(
    rows: Sequence[T], timestamps: Sequence[datetime], training_fraction: float = 0.7, validation_fraction: float = 0.15
) -> tuple[list[T], list[T], list[T]]:
    """Return chronological train/validation/test partitions; never randomize observations."""
    if len(rows) != len(timestamps) or len(rows) < 3:
        raise ValueError("rows and timestamps must have equal length of at least three")
    if not 0 < training_fraction < 1 or not 0 < validation_fraction < 1 or training_fraction + validation_fraction >= 1:
        raise ValueError("fractions must be positive and leave a test partition")
    ordered = [row for _, row in sorted(zip(timestamps, rows, strict=True), key=lambda item: item[0])]
    train_end = int(len(ordered) * training_fraction)
    validation_end = train_end + int(len(ordered) * validation_fraction)
    return ordered[:train_end], ordered[train_end:validation_end], ordered[validation_end:]


def summarize_evaluation(
    model_name: str, actual: Sequence[float], predicted: Sequence[float], baseline_predicted: Sequence[float]
) -> EvaluationSummary:
    return EvaluationSummary(
        model_name=model_name,
        row_count=len(actual),
        mae=mean_absolute_error(actual, predicted),
        rmse=root_mean_squared_error(actual, predicted),
        baseline_mae=mean_absolute_error(actual, baseline_predicted),
    )
