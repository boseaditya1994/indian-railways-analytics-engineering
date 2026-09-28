"""FastAPI application with server-side, read-only Snowflake mart access."""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from railway_pipeline.dashboard.service import (
    RailRadarLiveStatusRepository,
    SnowflakeDashboardMartRepository,
    UnavailableDashboardMartRepository,
)


def create_app() -> FastAPI:
    app = FastAPI(title="Rail Delay Dashboard API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
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

    @app.get("/v1/live/trains/{train_number}")
    def live_train_status(
        train_number: str,
        journey_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    ):
        return railradar_repository.get_live_status(train_number, journey_date)

    return app


app = create_app()
