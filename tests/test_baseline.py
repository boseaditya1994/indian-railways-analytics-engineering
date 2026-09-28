import pytest

from railway_pipeline.prediction.baseline import TrainRouteMeanBaseline
from railway_pipeline.prediction.metrics import mean_absolute_error, root_mean_squared_error


def test_train_route_baseline_prefers_specific_history() -> None:
    baseline = TrainRouteMeanBaseline().fit([("12345", "HWH", 10.0), ("12345", "HWH", 20.0), ("99999", "NDLS", 30.0)])
    assert baseline.predict("12345", "HWH") == 15.0
    assert baseline.predict("unknown", "unknown") == 20.0


def test_metrics_are_calculated() -> None:
    assert mean_absolute_error([10.0, 20.0], [12.0, 16.0]) == 3.0
    assert root_mean_squared_error([10.0, 20.0], [12.0, 16.0]) == pytest.approx(3.16227766)
