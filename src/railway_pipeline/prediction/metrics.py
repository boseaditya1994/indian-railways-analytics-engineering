"""Dependency-free model metrics for baseline and production comparison."""

from collections.abc import Sequence
from math import sqrt


def _validate(actual: Sequence[float], predicted: Sequence[float]) -> None:
    if not actual or len(actual) != len(predicted):
        raise ValueError("actual and predicted must be non-empty sequences of equal length")


def mean_absolute_error(actual: Sequence[float], predicted: Sequence[float]) -> float:
    _validate(actual, predicted)
    return sum(abs(value - estimate) for value, estimate in zip(actual, predicted, strict=True)) / len(actual)


def root_mean_squared_error(actual: Sequence[float], predicted: Sequence[float]) -> float:
    _validate(actual, predicted)
    return sqrt(sum((value - estimate) ** 2 for value, estimate in zip(actual, predicted, strict=True)) / len(actual))
