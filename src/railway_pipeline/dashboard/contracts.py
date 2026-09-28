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
