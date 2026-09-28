"""Archive a small, configured RailRadar live-status watchlist into Snowflake."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import requests
import snowflake.connector

from railway_pipeline.config.settings import Settings

ARCHIVE_TABLE = "RAIL_DELAY_ANALYTICS.LIVE.RAILRADAR_TRAIN_STATUS_SNAPSHOTS"
AUDIT_TABLE = "RAIL_DELAY_ANALYTICS.AUDIT.INGESTION_RUN_AUDIT"
SOURCE_NAME = "railradar_live_personal_portfolio"
CREDENTIAL_SERVICE = "indian-railways-analytics-engineering/raildar-archive"


def _load_local_env() -> None:
    """Load simple local settings without printing or committing secret values."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" not in line or line.lstrip().startswith("#"):
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip('"'))


def _train_numbers(values: list[str]) -> list[str]:
    numbers = [value.strip() for value in values if value.strip()]
    invalid = [number for number in numbers if not re.fullmatch(r"\d{5}", number)]
    if invalid:
        raise ValueError(f"Train numbers must be five digits: {', '.join(invalid)}")
    if not numbers:
        raise ValueError("Provide at least one --train number.")
    return list(dict.fromkeys(numbers))


def _credential_username(settings: Settings) -> str:
    if not settings.snowflake_account or not settings.snowflake_user:
        raise RuntimeError("SNOWFLAKE_ACCOUNT and SNOWFLAKE_USER are required in the local ignored .env file.")
    return f"{settings.snowflake_account}/{settings.snowflake_user}"


def _stored_snowflake_password(settings: Settings) -> str:
    try:
        import keyring
    except ImportError as exc:
        raise RuntimeError("Install the scheduler dependency: pip install -e '.[scheduler]'.") from exc
    password = keyring.get_password(CREDENTIAL_SERVICE, _credential_username(settings))
    if not password:
        raise RuntimeError(
            "Snowflake archive credential not found in Windows Credential Manager. "
            "Run scripts/setup_raildar_archive.ps1 once while logged in."
        )
    return password


def _top_rstgcn_watchlist(cursor, limit: int = 5) -> list[str]:
    cursor.execute(
        """
        SELECT TRAIN_NUMBER
        FROM RAIL_DELAY_ANALYTICS.ANALYTICS.FACT_STATION_ARRIVAL
        WHERE JOURNEY_DATE >= '2024-09-01' AND JOURNEY_DATE < '2024-10-01'
        GROUP BY TRAIN_NUMBER
        ORDER BY COUNT(*) DESC, TRAIN_NUMBER
        LIMIT %s
        """,
        (limit,),
    )
    trains = [str(row[0]) for row in cursor.fetchall()]
    if len(trains) != limit:
        raise RuntimeError(f"Expected {limit} RSTGCN watchlist trains, found {len(trains)}.")
    return trains


def _hash(payload: dict[str, object]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def main() -> None:
    _load_local_env()
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", action="append", default=[], help="Five-digit train number; repeat for a watchlist.")
    parser.add_argument(
        "--rstgcn-top-five",
        action="store_true",
        help="Use the five trains with the most September 2024 RSTGCN observations.",
    )
    args = parser.parse_args()
    if args.train and args.rstgcn_top_five:
        raise ValueError("Choose explicit --train values or --rstgcn-top-five, not both.")
    if not args.train and not args.rstgcn_top_five:
        raise ValueError("Provide --train values or use --rstgcn-top-five.")
    api_key = os.getenv("RAILRADAR_API_KEY")
    if not api_key:
        raise RuntimeError("RAILRADAR_API_KEY is required in the local ignored .env environment.")
    settings = Settings()
    password = _stored_snowflake_password(settings)
    run_id = str(uuid.uuid4())
    received = inserted = rejected = 0
    connection = snowflake.connector.connect(
        account=settings.snowflake_account, user=settings.snowflake_user, password=password,
        role=settings.snowflake_role, warehouse=settings.snowflake_warehouse, database=settings.snowflake_database,
    )
    try:
        cursor = connection.cursor()
        try:
            connection.execute_string(
                (Path(__file__).resolve().parents[1] / "snowflake/setup/003_live_raildar_archive.sql").read_text(
                    encoding="utf-8"
                )
            )
            cursor.execute(
                f"INSERT INTO {AUDIT_TABLE} (RUN_ID, PIPELINE_NAME, DATASET, SOURCE_NAME, STARTED_AT, STATUS) VALUES (%s,%s,%s,%s,CURRENT_TIMESTAMP(),%s)",
                (run_id, "railway_pipeline", "railradar_live_snapshots", SOURCE_NAME, "running"),
            )
            trains = _top_rstgcn_watchlist(cursor) if args.rstgcn_top_five else _train_numbers(args.train)
            for train_number in trains:
                response = requests.get(
                    f"https://api.railradar.in/v1/trains/{train_number}/live",
                    headers={"Authorization": f"Bearer {api_key}"}, params={"haltsOnly": "true"}, timeout=15,
                )
                if response.status_code != 200:
                    rejected += 1
                    continue
                data = response.json().get("data", {})
                received += 1
                retrieved_at = datetime.now(UTC)
                record = {
                    "train_number": str(data.get("trainNumber") or train_number), "journey_date": data.get("startDate"),
                    "provider_updated_at": data.get("lastUpdatedAt"), "journey_status": data.get("status"),
                    "delay_minutes": data.get("delayMinutes"), "current_station_code": (data.get("currentLocation") or {}).get("stationCode"),
                    "next_station_code": (data.get("nextHalt") or {}).get("stationCode"),
                    "next_station_name": (data.get("nextHalt") or {}).get("stationName"),
                    "retrieved_at": retrieved_at.isoformat(),
                }
                record_hash = _hash(record)
                cursor.execute(
                    f"""MERGE INTO {ARCHIVE_TABLE} target USING (SELECT %s AS SOURCE_RECORD_HASH) source
                    ON target.SOURCE_RECORD_HASH = source.SOURCE_RECORD_HASH
                    WHEN NOT MATCHED THEN INSERT (SNAPSHOT_ID,RUN_ID,SOURCE_NAME,TRAIN_NUMBER,JOURNEY_DATE,PROVIDER_UPDATED_AT,RETRIEVED_AT,JOURNEY_STATUS,DELAY_MINUTES,CURRENT_STATION_CODE,NEXT_STATION_CODE,NEXT_STATION_NAME,SOURCE_RECORD_HASH)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (record_hash, str(uuid.uuid4()), run_id, SOURCE_NAME, record["train_number"], record["journey_date"], record["provider_updated_at"], retrieved_at, record["journey_status"], record["delay_minutes"], record["current_station_code"], record["next_station_code"], record["next_station_name"], record_hash),
                )
                inserted += cursor.rowcount
            cursor.execute(
                f"UPDATE {AUDIT_TABLE} SET COMPLETED_AT=CURRENT_TIMESTAMP(), RECORDS_RECEIVED=%s, RECORDS_INSERTED=%s, RECORDS_REJECTED=%s, STATUS='succeeded' WHERE RUN_ID=%s",
                (received, inserted, rejected, run_id),
            )
            connection.commit()
        finally:
            cursor.close()
    finally:
        connection.close()
    print(f"RailRadar archive succeeded: run={run_id}; received={received}; inserted={inserted}; rejected={rejected}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"RailRadar archive failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
