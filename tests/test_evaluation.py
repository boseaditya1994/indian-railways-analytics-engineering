from datetime import datetime, timedelta

import pytest

from railway_pipeline.prediction.evaluation import chronological_split, summarize_evaluation


def test_chronological_split_orders_before_partitioning() -> None:
    timestamps = [datetime(2025, 1, 3) + timedelta(days=offset) for offset in (2, 0, 3, 1, 4, 5, 6, 7, 8, 9)]
    rows = list(range(10))
    train, validation, test = chronological_split(rows, timestamps)
    assert train == [1, 3, 0, 2, 4, 5, 6]
    assert validation == [7]
    assert test == [8, 9]


def test_evaluation_comparison_requires_model_to_beat_baseline() -> None:
    result = summarize_evaluation("candidate", [10.0, 20.0], [11.0, 21.0], [15.0, 25.0])
    assert result.improves_on_baseline
    assert result.mae == 1.0


def test_invalid_split_is_rejected() -> None:
    with pytest.raises(ValueError):
        chronological_split([1, 2], [datetime.now(), datetime.now()])
