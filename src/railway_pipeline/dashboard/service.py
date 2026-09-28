"""Repository boundary for dashboard marts, deliberately independent from API routes."""

from __future__ import annotations

import os
import re
import time
from typing import Protocol

import requests

from railway_pipeline.dashboard.contracts import (
    DataStatus,
    LiveTrainStatus,
    NetworkOverview,
    PipelineHealth,
    PredictionSummary,
)


class DashboardMartRepository(Protocol):
    def network_overview(self) -> NetworkOverview: ...

    def pipeline_health(self) -> PipelineHealth: ...


class UnavailableDashboardMartRepository:
    """Safe default before an approved source and successful warehouse run exist."""

    status = DataStatus(
        state="awaiting_approved_source",
        message="No approved historical source has been ingested; dashboard metrics are unavailable.",
    )

    def network_overview(self) -> NetworkOverview:
        return NetworkOverview(data_status=self.status)

    def pipeline_health(self) -> PipelineHealth:
        return PipelineHealth(data_status=self.status)

    def insights_unavailable(self) -> dict[str, object]:
        return {"data_status": self.status}


class SnowflakeDashboardMartRepository:
    """Read-only, server-side access to published Snowflake marts.

    The password is intentionally read only from the process environment; it is
    never added to an API response, client bundle, repository file, or log.
    """

    def __init__(self) -> None:
        self.password = os.getenv("SNOWFLAKE_PASSWORD")
        self.account = os.getenv("SNOWFLAKE_ACCOUNT")
        self.user = os.getenv("SNOWFLAKE_USER")
        self.role = os.getenv("SNOWFLAKE_ROLE", "RAIL_DELAY_DASHBOARD_READER")
        self.warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH")

    @property
    def configured(self) -> bool:
        return bool(self.password and self.account and self.user)

    def _connection(self):
        import snowflake.connector

        return snowflake.connector.connect(
            account=self.account,
            user=self.user,
            password=self.password,
            role=self.role,
            warehouse=self.warehouse,
            database="RAIL_DELAY_ANALYTICS",
            schema="ANALYTICS",
        )

    @staticmethod
    def _unavailable_status() -> DataStatus:
        return DataStatus(
            state="warehouse_unavailable",
            message="Published dashboard metrics are temporarily unavailable."
        )

    def network_overview(self) -> NetworkOverview:
        if not self.configured:
            return NetworkOverview(
                data_status=DataStatus(
                    state="not_configured",
                    message="Dashboard server credentials have not been configured.",
                )
            )
        try:
            with self._connection() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        COUNT(DISTINCT CONCAT(TRAIN_NUMBER, '|', JOURNEY_DATE::VARCHAR)),
                        COUNT(*),
                        AVG(ARRIVAL_DELAY_MINUTES),
                        MEDIAN(ARRIVAL_DELAY_MINUTES),
                        AVG(IFF(ARRIVAL_DELAY_MINUTES <= 0, 1, 0)) * 100,
                        MIN(JOURNEY_DATE), MAX(JOURNEY_DATE)
                    FROM RAIL_DELAY_ANALYTICS.ANALYTICS.FACT_STATION_ARRIVAL
                    WHERE ARRIVAL_DELAY_MINUTES IS NOT NULL
                    """
                )
                journeys, observations, average, median, on_time, coverage_start, coverage_end = cursor.fetchone()
                cursor.execute("SELECT COUNT(*) FROM RAIL_DELAY_ANALYTICS.ANALYTICS.DIM_STATION")
                stations = cursor.fetchone()[0]
                cursor.execute(
                    """
                    SELECT COMPLETED_AT
                    FROM RAIL_DELAY_ANALYTICS.AUDIT.INGESTION_RUN_AUDIT
                    WHERE STATUS = 'succeeded' AND SOURCE_NAME = 'rstgcn_sep2024'
                    ORDER BY COMPLETED_AT DESC
                    LIMIT 1
                    """
                )
                latest = cursor.fetchone()
            return NetworkOverview(
                data_status=DataStatus(
                    state="ready",
                    message="Metrics are calculated from the approved RSTGCN September 2024 source.",
                    last_successful_pipeline_at=latest[0] if latest else None,
                ),
                journeys_analysed=int(journeys or 0),
                stations=int(stations or 0),
                average_arrival_delay_minutes=float(average) if average is not None else None,
                median_arrival_delay_minutes=float(median) if median is not None else None,
                on_time_or_early_percent=float(on_time) if on_time is not None else None,
                station_stop_observations=int(observations or 0),
                coverage_start_date=coverage_start.isoformat() if coverage_start else None,
                coverage_end_date=coverage_end.isoformat() if coverage_end else None,
            )
        except Exception:
            return NetworkOverview(data_status=self._unavailable_status())

    def pipeline_health(self) -> PipelineHealth:
        if not self.configured:
            return PipelineHealth(
                data_status=DataStatus(
                    state="not_configured",
                    message="Dashboard server credentials have not been configured.",
                )
            )
        try:
            with self._connection() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COMPLETED_AT, STATUS, RECORDS_RECEIVED, RECORDS_REJECTED
                    FROM RAIL_DELAY_ANALYTICS.AUDIT.INGESTION_RUN_AUDIT
                    WHERE DATASET = 'train_running_events' AND SOURCE_NAME = 'rstgcn_sep2024'
                    ORDER BY STARTED_AT DESC
                    LIMIT 1
                    """
                )
                row = cursor.fetchone()
            if not row:
                return PipelineHealth(data_status=self._unavailable_status())
            return PipelineHealth(
                data_status=DataStatus(
                    state="ready",
                    message="Latest approved-source ingestion audit is available.",
                    last_successful_pipeline_at=row[0],
                ),
                last_run_status=str(row[1]),
                records_received=int(row[2] or 0),
                records_rejected=int(row[3] or 0),
            )
        except Exception:
            return PipelineHealth(data_status=self._unavailable_status())

    def prediction_summary(self) -> PredictionSummary:
        if not self.configured:
            return PredictionSummary(data_status=DataStatus(state="not_configured", message="Dashboard server credentials have not been configured."))
        try:
            with self._connection() as connection, connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EVALUATED_AT, VALIDATION_ROW_COUNT, MAE, RMSE, BASELINE_MAE, ACCEPTED_FOR_PREDICTION, MODEL_NAME
                    FROM RAIL_DELAY_ANALYTICS.ML.MODEL_EVALUATION_AUDIT ORDER BY EVALUATED_AT DESC LIMIT 1
                """)
                row = cursor.fetchone()
            if not row:
                return PredictionSummary(data_status=DataStatus(state="not_evaluated", message="No chronologically evaluated prediction baseline is available yet."))
            return PredictionSummary(
                data_status=DataStatus(state="ready", message="Metrics are from an untouched chronological holdout.", last_successful_pipeline_at=row[0]),
                evaluation_rows=int(row[1]), mae_minutes=float(row[2]), rmse_minutes=float(row[3]),
                global_mean_mae_minutes=float(row[4]), accepted_for_prediction=bool(row[5]), model_name=str(row[6]),
            )
        except Exception:
            return PredictionSummary(data_status=self._unavailable_status())

    def delay_distribution(self) -> dict[str, object]:
        try:
            with self._connection() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        CASE
                            WHEN ARRIVAL_DELAY_MINUTES <= 0 THEN 'On time / early'
                            WHEN ARRIVAL_DELAY_MINUTES <= 15 THEN '1–15 min'
                            WHEN ARRIVAL_DELAY_MINUTES <= 30 THEN '16–30 min'
                            WHEN ARRIVAL_DELAY_MINUTES <= 60 THEN '31–60 min'
                            ELSE '60+ min'
                        END AS DELAY_BAND,
                        CASE
                            WHEN ARRIVAL_DELAY_MINUTES <= 0 THEN 1
                            WHEN ARRIVAL_DELAY_MINUTES <= 15 THEN 2
                            WHEN ARRIVAL_DELAY_MINUTES <= 30 THEN 3
                            WHEN ARRIVAL_DELAY_MINUTES <= 60 THEN 4
                            ELSE 5
                        END AS BAND_ORDER,
                        COUNT(*) AS OBSERVATIONS
                    FROM RAIL_DELAY_ANALYTICS.ANALYTICS.FACT_STATION_ARRIVAL
                    WHERE ARRIVAL_DELAY_MINUTES IS NOT NULL
                    GROUP BY DELAY_BAND, BAND_ORDER
                    ORDER BY BAND_ORDER
                    """
                )
                rows = cursor.fetchall()
            return {
                "data_status": DataStatus(state="ready", message="Delay bands are from RSTGCN September 2024."),
                "bands": [{"label": str(row[0]), "observations": int(row[2])} for row in rows],
            }
        except Exception:
            return {"data_status": self._unavailable_status(), "bands": []}

    def station_hotspots(self, limit: int) -> dict[str, object]:
        try:
            with self._connection() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT STATION_CODE, COUNT(*) AS OBSERVATIONS,
                           AVG(ARRIVAL_DELAY_MINUTES) AS AVERAGE_DELAY,
                           MEDIAN(ARRIVAL_DELAY_MINUTES) AS MEDIAN_DELAY,
                           AVG(IFF(ARRIVAL_DELAY_MINUTES <= 0, 1, 0)) * 100 AS ON_TIME_PERCENT
                    FROM RAIL_DELAY_ANALYTICS.ANALYTICS.FACT_STATION_ARRIVAL
                    WHERE ARRIVAL_DELAY_MINUTES IS NOT NULL
                    GROUP BY STATION_CODE
                    HAVING COUNT(*) >= 30
                    ORDER BY AVERAGE_DELAY DESC, OBSERVATIONS DESC, STATION_CODE
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cursor.fetchall()
            return {
                "data_status": DataStatus(state="ready", message="Station rankings require at least 30 observations."),
                "stations": [
                    {"station_code": str(row[0]), "observations": int(row[1]), "average_delay_minutes": float(row[2]), "median_delay_minutes": float(row[3]), "on_time_percent": float(row[4])}
                    for row in rows
                ],
            }
        except Exception:
            return {"data_status": self._unavailable_status(), "stations": []}

    def daily_trend(self) -> dict[str, object]:
        try:
            with self._connection() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT JOURNEY_DATE, COUNT(*), AVG(ARRIVAL_DELAY_MINUTES), MEDIAN(ARRIVAL_DELAY_MINUTES)
                    FROM RAIL_DELAY_ANALYTICS.ANALYTICS.FACT_STATION_ARRIVAL
                    WHERE ARRIVAL_DELAY_MINUTES IS NOT NULL
                    GROUP BY JOURNEY_DATE
                    ORDER BY JOURNEY_DATE
                    """
                )
                rows = cursor.fetchall()
            return {
                "data_status": DataStatus(state="ready", message="Daily aggregates cover September 2024 only."),
                "days": [{"journey_date": row[0].isoformat(), "observations": int(row[1]), "average_delay_minutes": float(row[2]), "median_delay_minutes": float(row[3])} for row in rows],
            }
        except Exception:
            return {"data_status": self._unavailable_status(), "days": []}

    def train_profile(self, train_number: str) -> dict[str, object]:
        try:
            with self._connection() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(DISTINCT JOURNEY_DATE), COUNT(*), AVG(ARRIVAL_DELAY_MINUTES),
                           MEDIAN(ARRIVAL_DELAY_MINUTES), AVG(IFF(ARRIVAL_DELAY_MINUTES <= 0, 1, 0)) * 100
                    FROM RAIL_DELAY_ANALYTICS.ANALYTICS.FACT_STATION_ARRIVAL
                    WHERE TRAIN_NUMBER = %s AND ARRIVAL_DELAY_MINUTES IS NOT NULL
                    """,
                    (train_number,),
                )
                row = cursor.fetchone()
            if not row or not row[1]:
                return {"data_status": DataStatus(state="not_found", message="No RSTGCN September 2024 observations exist for that train number.")}
            return {
                "data_status": DataStatus(state="ready", message="Historical RSTGCN September 2024 train profile."),
                "train_number": train_number, "journeys": int(row[0]), "observations": int(row[1]),
                "average_delay_minutes": float(row[2]), "median_delay_minutes": float(row[3]), "on_time_percent": float(row[4]),
            }
        except Exception:
            return {"data_status": self._unavailable_status()}

    def prospective_archive_summary(self) -> dict[str, object]:
        try:
            with self._connection() as connection, connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*), COUNT(DISTINCT TRAIN_NUMBER), MIN(RETRIEVED_AT), MAX(RETRIEVED_AT), AVG(DELAY_MINUTES)
                    FROM RAIL_DELAY_ANALYTICS.LIVE.RAILRADAR_TRAIN_STATUS_SNAPSHOTS
                    """
                )
                row = cursor.fetchone()
            return {
                "data_status": DataStatus(state="ready", message="Prospective RailRadar snapshots are separate from RSTGCN history."),
                "snapshots": int(row[0]), "trains": int(row[1]), "first_retrieved_at": row[2], "latest_retrieved_at": row[3],
                "average_delay_minutes": float(row[4]) if row[4] is not None else None,
            }
        except Exception:
            return {"data_status": DataStatus(state="not_started", message="Prospective RailRadar archive is not available yet.")}


class RailRadarLiveStatusRepository:
    """On-demand RailRadar lookup with a small in-memory cache and no persistence."""

    endpoint_template = "https://api.railradar.in/v1/trains/{train_number}/live"
    cache_ttl_seconds = 30

    def __init__(self, session: requests.Session | None = None) -> None:
        self.api_key = os.getenv("RAILRADAR_API_KEY")
        self.session = session or requests.Session()
        self._cache: dict[tuple[str, str | None], tuple[float, LiveTrainStatus]] = {}

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def get_live_status(self, train_number: str, journey_date: str | None = None) -> LiveTrainStatus:
        if not re.fullmatch(r"\d{5}", train_number):
            return LiveTrainStatus(
                data_status=DataStatus(state="invalid_request", message="Train number must contain exactly five digits.")
            )
        if not self.configured:
            return LiveTrainStatus(
                data_status=DataStatus(
                    state="not_configured", message="RailRadar live-status key is not configured on the API server."
                )
            )
        cache_key = (train_number, journey_date)
        cached = self._cache.get(cache_key)
        if cached and time.monotonic() - cached[0] < self.cache_ttl_seconds:
            return cached[1].model_copy(update={"cached": True})
        try:
            params: dict[str, str] = {"haltsOnly": "true"}
            if journey_date:
                params["date"] = journey_date
            response = self.session.get(
                self.endpoint_template.format(train_number=train_number),
                headers={"Authorization": f"Bearer {self.api_key}"},
                params=params,
                timeout=15,
            )
            if response.status_code == 429:
                return LiveTrainStatus(
                    data_status=DataStatus(
                        state="rate_limited", message="RailRadar request limit reached; please retry later."
                    )
                )
            response.raise_for_status()
            payload = response.json().get("data", {})
            next_halt = payload.get("nextHalt") or {}
            current_location = payload.get("currentLocation") or {}
            status = LiveTrainStatus(
                data_status=DataStatus(
                    state="ready",
                    message="Live snapshot supplied by RailRadar; it is not persisted as historical data.",
                ),
                train_number=str(payload.get("trainNumber") or train_number),
                train_name=payload.get("trainName"),
                journey_date=payload.get("startDate"),
                status=payload.get("status"),
                delay_minutes=payload.get("delayMinutes"),
                current_station_code=current_location.get("stationCode"),
                next_station_code=next_halt.get("stationCode"),
                next_station_name=next_halt.get("stationName"),
                provider_updated_at=payload.get("lastUpdatedAt"),
            )
            self._cache[cache_key] = (time.monotonic(), status)
            return status
        except requests.RequestException:
            return LiveTrainStatus(
                data_status=DataStatus(
                    state="provider_unavailable", message="Live status is temporarily unavailable from RailRadar."
                )
            )
