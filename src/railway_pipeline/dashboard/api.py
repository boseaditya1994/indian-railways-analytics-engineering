"""FastAPI application with server-side, read-only Snowflake mart access."""

import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from railway_pipeline.dashboard.service import (
    RailRadarLiveStatusRepository,
    SnowflakeDashboardMartRepository,
    UnavailableDashboardMartRepository,
)


def create_app() -> FastAPI:
    app = FastAPI(title="Rail Delay Dashboard API", version="0.1.0")
    default_origins = "http://127.0.0.1:5173,http://localhost:5173"
    cors_origins = os.getenv("DASHBOARD_CORS_ORIGINS", default_origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in cors_origins.split(",") if origin.strip()],
        allow_methods=["GET"],
        allow_headers=[],
    )
    snowflake_repository = SnowflakeDashboardMartRepository()
    repository = snowflake_repository if snowflake_repository.configured else UnavailableDashboardMartRepository()
    railradar_repository = RailRadarLiveStatusRepository()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/dashboard/network-overview")
    def network_overview():
        return repository.network_overview()

    @app.get("/v1/dashboard/pipeline-health")
    def pipeline_health():
        return repository.pipeline_health()

    @app.get("/v1/dashboard/prediction-summary")
    def prediction_summary():
        return repository.prediction_summary()

    @app.get("/v1/dashboard/delay-distribution")
    def delay_distribution():
        return repository.delay_distribution() if hasattr(repository, "delay_distribution") else repository.insights_unavailable()

    @app.get("/v1/dashboard/station-hotspots")
    def station_hotspots(limit: int = Query(default=10, ge=1, le=25)):
        return repository.station_hotspots(limit) if hasattr(repository, "station_hotspots") else repository.insights_unavailable()

    @app.get("/v1/dashboard/daily-trend")
    def daily_trend():
        return repository.daily_trend() if hasattr(repository, "daily_trend") else repository.insights_unavailable()

    @app.get("/v1/dashboard/trains/{train_number}")
    def train_profile(train_number: str):
        if not train_number.isdigit() or len(train_number) != 5:
            raise HTTPException(status_code=422, detail="Train number must contain exactly five digits.")
        return repository.train_profile(train_number) if hasattr(repository, "train_profile") else repository.insights_unavailable()

    @app.get("/v1/dashboard/prospective-archive")
    def prospective_archive():
        return repository.prospective_archive_summary() if hasattr(repository, "prospective_archive_summary") else repository.insights_unavailable()

    @app.get("/v1/live/trains/{train_number}")
    def live_train_status(
        train_number: str,
        journey_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    ):
        return railradar_repository.get_live_status(train_number, journey_date)

    return app


app = create_app()
