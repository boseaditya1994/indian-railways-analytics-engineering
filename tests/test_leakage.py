from datetime import datetime, timedelta

import pytest

from railway_pipeline.features.leakage import assert_feature_available


def test_feature_at_prediction_time_is_valid() -> None:
    moment = datetime(2025, 1, 1, 12)
    assert_feature_available(moment, moment)


def test_future_feature_is_rejected() -> None:
    moment = datetime(2025, 1, 1, 12)
    with pytest.raises(ValueError, match="leakage"):
        assert_feature_available(moment + timedelta(seconds=1), moment)
