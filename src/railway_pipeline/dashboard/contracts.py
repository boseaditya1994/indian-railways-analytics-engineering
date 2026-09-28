"""Stable response shapes shared by the dashboard API and React client."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DataStatus(BaseModel):
    state: str
    message: str
    last_successful_pipeline_at: datetime | None = None


class NetworkOverview(BaseModel):
    data_status: DataStatus
    journeys_analysed: int | None = None
    stations: int | None = None
    average_arrival_delay_minutes: float | None = None
    median_arrival_delay_minutes: float | None = None
    on_time_or_early_percent: float | None = None


class PipelineHealth(BaseModel):
    data_status: DataStatus
    last_run_status: str | None = None
    records_received: int | None = None
    records_rejected: int | None = None


class LiveTrainStatus(BaseModel):
    """A non-persisted, provider-attributed current train snapshot."""

    data_status: DataStatus
    train_number: str | None = None
    train_name: str | None = None
    journey_date: str | None = None
    status: str | None = None
    delay_minutes: float | None = None
    current_station_code: str | None = None
    next_station_code: str | None = None
    next_station_name: str | None = None
    provider_updated_at: datetime | None = None
    cached: bool = False
