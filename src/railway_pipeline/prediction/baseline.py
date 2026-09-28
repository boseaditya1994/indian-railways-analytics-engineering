"""Transparent historical-mean baseline used before any ML model is considered."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field


@dataclass
class TrainRouteMeanBaseline:
    global_mean: float = 0.0
    means: dict[tuple[str, str], float] = field(default_factory=dict)

    def fit(self, observations: Iterable[tuple[str, str, float]]) -> "TrainRouteMeanBaseline":
        totals: dict[tuple[str, str], float] = defaultdict(float)
        counts: dict[tuple[str, str], int] = defaultdict(int)
        all_values: list[float] = []
        for train_number, station_code, delay in observations:
            totals[(train_number, station_code)] += delay
            counts[(train_number, station_code)] += 1
            all_values.append(delay)
        if not all_values:
            raise ValueError("at least one historical delay is required")
        self.global_mean = sum(all_values) / len(all_values)
        self.means = {key: totals[key] / counts[key] for key in totals}
        return self

    def predict(self, train_number: str, station_code: str) -> float:
        return self.means.get((train_number, station_code), self.global_mean)
