"""Idempotently load the RSTGCN route file into the raw schedule table."""

from __future__ import annotations

import csv
import getpass
import hashlib
import json
import sys
import uuid
from pathlib import Path

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

from railway_pipeline.config.settings import Settings

ROOT = Path(__file__).resolve().parents[1]
RAW_TABLE = "RAIL_DELAY_ANALYTICS.RAW.TRAIN_SCHEDULE_STOPS"
AUDIT_TABLE = "RAIL_DELAY_ANALYTICS.AUDIT.INGESTION_RUN_AUDIT"
STAGE_TABLE = "RSTGCN_SCHEDULE_STOPS_STAGE"


def _key(value: object) -> str:
    text = str(value or "").strip().upper()
    return text[:-2] if text.endswith(".0") else text


def _number(value: object) -> float | None:
    text = str(value or "").strip()
    return float(text) if text else None


def _hash(record: dict[str, object]) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _find_route_path() -> Path:
    matches = list((ROOT / "data" / "raw" / "rstgcn_sep2024").rglob("train_routes_Sep2024.csv"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one route CSV; found {len(matches)}")
    return matches[0]


def main() -> None:
    route_path = _find_route_path()
    settings = Settings()
    password = getpass.getpass("Snowflake password (not saved): ")
    run_id = str(uuid.uuid4())
    received = 0
    connection = snowflake.connector.connect(
        account=settings.snowflake_account, user=settings.snowflake_user, password=password,
        role=settings.snowflake_role, warehouse=settings.snowflake_warehouse, database=settings.snowflake_database,
    )
    cursor = connection.cursor()
    try:
        cursor.execute("USE DATABASE RAIL_DELAY_ANALYTICS")
        cursor.execute("USE SCHEMA RAW")
        cursor.execute(
            f"INSERT INTO {AUDIT_TABLE} (RUN_ID, PIPELINE_NAME, DATASET, SOURCE_NAME, STARTED_AT, STATUS) "
            "VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP(), %s)",
            (run_id, "railway_pipeline", "train_schedule_stops", "rstgcn_sep2024", "running"),
        )
        cursor.execute(f"CREATE OR REPLACE TEMPORARY TABLE {STAGE_TABLE} LIKE {RAW_TABLE}")
        batch: list[dict[str, object]] = []
        with route_path.open("r", encoding="utf-8-sig", newline="") as route_file:
            for row in csv.DictReader(route_file):
                received += 1
                record = {
                    "TRAIN_NUMBER": _key(row.get("trainNumber")),
                    "TRAIN_NAME": str(row.get("trainName") or "").strip() or None,
                    "TRAIN_TYPE": None,
                    "SOURCE_STATION_CODE": None,
                    "DESTINATION_STATION_CODE": None,
                    "STATION_CODE": _key(row.get("station_code")),
                    "STATION_NAME": str(row.get("station_name") or "").strip() or None,
                    "STATION_SEQUENCE": int(float(str(row.get("stnSerialNumber") or "0"))),
                    "SCHEDULE_ARRIVAL_TIME": str(row.get("arrivalTime") or "").strip() or None,
                    "SCHEDULE_DEPARTURE_TIME": str(row.get("departureTime") or "").strip() or None,
                    "JOURNEY_DAY_NUMBER": None,
                    "DISTANCE_KM": _number(row.get("distance")),
                    "SOURCE_NAME": "rstgcn_sep2024",
                    "RUN_ID": run_id,
                }
                record["SOURCE_RECORD_HASH"] = _hash(record)
                batch.append(record)
                if len(batch) == 25_000:
                    success, _, _, output = write_pandas(connection, pd.DataFrame(batch), STAGE_TABLE, quote_identifiers=False)
                    if not success:
                        raise RuntimeError(f"Snowflake bulk upload failed: {output}")
                    batch = []
        if batch:
            success, _, _, output = write_pandas(connection, pd.DataFrame(batch), STAGE_TABLE, quote_identifiers=False)
            if not success:
                raise RuntimeError(f"Snowflake bulk upload failed: {output}")
        source = f"(SELECT * FROM {STAGE_TABLE} QUALIFY ROW_NUMBER() OVER (PARTITION BY SOURCE_RECORD_HASH ORDER BY TRAIN_NUMBER, STATION_SEQUENCE) = 1)"
        cursor.execute(f"SELECT COUNT(*) FROM {source}")
        distinct_rows = int(cursor.fetchone()[0])
        cursor.execute(f"SELECT COUNT(*) FROM {source} s JOIN {RAW_TABLE} t ON t.SOURCE_RECORD_HASH = s.SOURCE_RECORD_HASH")
        already_present = int(cursor.fetchone()[0])
        cursor.execute(
            f"MERGE INTO {RAW_TABLE} t USING {source} s ON t.SOURCE_RECORD_HASH = s.SOURCE_RECORD_HASH "
            "WHEN NOT MATCHED THEN INSERT (TRAIN_NUMBER, TRAIN_NAME, TRAIN_TYPE, SOURCE_STATION_CODE, DESTINATION_STATION_CODE, "
            "STATION_CODE, STATION_NAME, STATION_SEQUENCE, SCHEDULE_ARRIVAL_TIME, SCHEDULE_DEPARTURE_TIME, JOURNEY_DAY_NUMBER, "
            "DISTANCE_KM, SOURCE_NAME, SOURCE_RECORD_HASH, RUN_ID) VALUES (s.TRAIN_NUMBER, s.TRAIN_NAME, s.TRAIN_TYPE, "
            "s.SOURCE_STATION_CODE, s.DESTINATION_STATION_CODE, s.STATION_CODE, s.STATION_NAME, s.STATION_SEQUENCE, "
            "s.SCHEDULE_ARRIVAL_TIME, s.SCHEDULE_DEPARTURE_TIME, s.JOURNEY_DAY_NUMBER, s.DISTANCE_KM, s.SOURCE_NAME, "
            "s.SOURCE_RECORD_HASH, s.RUN_ID)"
        )
        inserted = distinct_rows - already_present
        cursor.execute(
            f"UPDATE {AUDIT_TABLE} SET COMPLETED_AT=CURRENT_TIMESTAMP(), RECORDS_RECEIVED=%s, RECORDS_INSERTED=%s, "
            "RECORDS_REJECTED=0, STATUS='succeeded' WHERE RUN_ID=%s",
            (received, inserted, run_id),
        )
        connection.commit()
        print("RSTGCN schedule load succeeded")
        print(f"Run ID: {run_id}")
        print(f"Rows received: {received}")
        print(f"Distinct schedule stops: {distinct_rows}")
        print(f"Inserted: {inserted}")
        print(f"Already present: {already_present}")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"RSTGCN schedule load failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
