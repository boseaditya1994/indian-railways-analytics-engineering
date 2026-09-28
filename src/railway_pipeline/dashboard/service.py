"""Repository boundary for dashboard marts, deliberately independent from API routes."""

from __future__ import annotations

import os
from typing import Protocol

from railway_pipeline.dashboard.contracts import DataStatus, NetworkOverview, PipelineHealth


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


class SnowflakeDashboardMartRepository:
    """Read-only, server-side access to published Snowflake marts.

    The password is intentionally read only from the process environment; it is
    never added to an API response, client bundle, repository file, or log.
    """

    def __init__(self) -> None:
        self.password = os.getenv("SNOWFLAKE_PASSWORD")
        self.account = os.getenv("SNOWFLAKE_ACCOUNT")
        self.user = os.getenv("SNOWFLAKE_USER")
        self.role = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")
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
                        AVG(ARRIVAL_DELAY_MINUTES),
                        MEDIAN(ARRIVAL_DELAY_MINUTES),
                        AVG(IFF(ARRIVAL_DELAY_MINUTES <= 0, 1, 0)) * 100
                    FROM RAIL_DELAY_ANALYTICS.ANALYTICS.FACT_STATION_ARRIVAL
                    WHERE ARRIVAL_DELAY_MINUTES IS NOT NULL
                    """
                )
                journeys, average, median, on_time = cursor.fetchone()
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
