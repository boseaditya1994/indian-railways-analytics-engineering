"""Simple invariants that prevent feature values from arriving after prediction time."""

from datetime import datetime


def assert_feature_available(feature_observed_at: datetime | None, prediction_at: datetime) -> None:
    """Reject a feature derived after the prediction point; null may represent schedule-only data."""
    if feature_observed_at is not None and feature_observed_at > prediction_at:
        raise ValueError("feature observation occurs after prediction time (target leakage risk)")
