"""Canonical, source-agnostic train running event contract."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TrainRunningEvent(BaseModel):
    """One observed train journey station stop; missing actual times remain missing."""

    model_config = ConfigDict(str_strip_whitespace=True)

    train_number: str = Field(min_length=1, max_length=16)
    journey_date: date
    station_code: str = Field(min_length=1, max_length=16)
    station_sequence: int = Field(gt=0)
    source_name: str = Field(min_length=1, max_length=100)
    source_observed_at: datetime | None = None
    scheduled_arrival_at: datetime | None = None
    actual_arrival_at: datetime | None = None
    scheduled_departure_at: datetime | None = None
    actual_departure_at: datetime | None = None
    arrival_delay_minutes: float | None = None
    departure_delay_minutes: float | None = None
    status: str | None = None

    @field_validator("train_number", "station_code")
    @classmethod
    def normalize_identifiers(cls, value: str) -> str:
        return value.upper()

    @field_validator("arrival_delay_minutes", "departure_delay_minutes")
    @classmethod
    def reject_impossible_delays(cls, value: float | None) -> float | None:
        if value is not None and not -1_440 <= value <= 10_080:
            raise ValueError("delay must be within -1440 and 10080 minutes")
        return value
