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
    station_stop_observations: int | None = None
    coverage_start_date: str | None = None
    coverage_end_date: str | None = None


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


class PredictionSummary(BaseModel):
    data_status: DataStatus
    model_name: str | None = None
    evaluation_rows: int | None = None
    mae_minutes: float | None = None
    rmse_minutes: float | None = None
    global_mean_mae_minutes: float | None = None
    accepted_for_prediction: bool | None = None
