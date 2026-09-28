"""Chunked, idempotent loader for the approved RSTGCN September 2024 files."""

from __future__ import annotations

import csv
import hashlib
import json
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import ValidationError
from snowflake.connector import SnowflakeConnection
from snowflake.connector.pandas_tools import write_pandas

from railway_pipeline.models.running_event import TrainRunningEvent


RAW_TABLE = "RAIL_DELAY_ANALYTICS.RAW.TRAIN_RUNNING_EVENTS"
AUDIT_TABLE = "RAIL_DELAY_ANALYTICS.AUDIT.INGESTION_RUN_AUDIT"
STAGE_TABLE = "RSTGCN_RUNNING_EVENTS_STAGE"
RAW_DATABASE = "RAIL_DELAY_ANALYTICS"
RAW_SCHEMA = "RAW"
SOURCE_TIME_MIGRATIONS = (
    f"ALTER TABLE {RAW_TABLE} ADD COLUMN IF NOT EXISTS SOURCE_SCHEDULED_ARRIVAL_TIME VARCHAR",
    f"ALTER TABLE {RAW_TABLE} ADD COLUMN IF NOT EXISTS SOURCE_ACTUAL_ARRIVAL_TIME VARCHAR",
    f"ALTER TABLE {RAW_TABLE} ADD COLUMN IF NOT EXISTS SOURCE_SCHEDULED_DEPARTURE_TIME VARCHAR",
    f"ALTER TABLE {RAW_TABLE} ADD COLUMN IF NOT EXISTS SOURCE_ACTUAL_DEPARTURE_TIME VARCHAR",
)


@dataclass(frozen=True)
class LoadResult:
    """Counts and identifier for one warehouse load attempt."""

    run_id: str
    received: int
    valid: int
    rejected: int
    distinct_valid: int
    inserted: int
    already_present: int
    quarantine_path: Path


def _value_as_str(value: Any) -> str | None:
    if value is None:
        return None
    value_str = str(value).strip()
    return value_str or None


def _source_record_hash(record: dict[str, Any]) -> str:
    """Return a stable content hash for idempotent source-record ingestion."""
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _key(value: Any) -> str:
    """Normalise CSV join keys without changing meaningful train identifiers."""
    text = str(value or "").strip().upper()
    return text[:-2] if text.endswith(".0") else text


def _optional_number(value: Any) -> float | None:
    text = str(value or "").strip()
    return float(text) if text else None


def _route_sequences(route_path: Path) -> dict[tuple[str, str], int]:
    """Build the source train/station to stop-sequence lookup from the route file."""
    sequences: dict[tuple[str, str], int] = {}
    with route_path.open("r", encoding="utf-8-sig", newline="") as route_file:
        for row in csv.DictReader(route_file):
            train = _key(row.get("trainNumber"))
            station_code = _key(row.get("station_code"))
            station_name = _key(row.get("station_name"))
            serial = str(row.get("stnSerialNumber") or "").strip()
            if not train or not serial:
                continue
            try:
                sequence = int(float(serial))
            except ValueError:
                continue
            if station_code:
                sequences.setdefault((train, station_code), sequence)
            if station_name:
                sequences.setdefault((train, station_name), sequence)
    return sequences


def _iter_rstgcn_records(delay_path: Path, route_path: Path) -> Iterator[dict[str, Any]]:
    """Yield canonical records from the two public RSTGCN September 2024 CSVs."""
    sequences = _route_sequences(route_path)
    with delay_path.open("r", encoding="utf-8-sig", newline="") as delay_file:
        for row in csv.DictReader(delay_file):
            train_number = _key(row.get("train"))
            station = _key(row.get("station"))
            yield {
                "train_number": train_number,
                "journey_date": row.get("date"),
                "station_code": station,
                "station_sequence": sequences.get((train_number, station), 0),
                "scheduled_arrival_at": None,
                "actual_arrival_at": None,
                "scheduled_departure_at": None,
                "actual_departure_at": None,
                "arrival_delay_minutes": _optional_number(row.get("arr_delay")),
                "departure_delay_minutes": _optional_number(row.get("dep_delay")),
                "status": "observed",
                "source_name": "rstgcn_sep2024",
                "source_scheduled_arrival_time": row.get("sch_arr"),
                "source_actual_arrival_time": row.get("act_arr"),
                "source_scheduled_departure_time": row.get("sch_dep"),
                "source_actual_departure_time": row.get("act_dep"),
            }


def _warehouse_row(event: TrainRunningEvent, raw: dict[str, Any], run_id: str) -> dict[str, Any]:
    """Map a validated canonical record to the raw Snowflake table contract."""
    return {
        "TRAIN_NUMBER": event.train_number,
        "JOURNEY_DATE": event.journey_date,
        "STATION_CODE": event.station_code,
        "STATION_SEQUENCE": event.station_sequence,
        # Do not manufacture timestamps from source strings whose timezone/date is unknown.
        "SCHEDULED_ARRIVAL_AT": None,
        "ACTUAL_ARRIVAL_AT": None,
        "SCHEDULED_DEPARTURE_AT": None,
        "ACTUAL_DEPARTURE_AT": None,
        "ARRIVAL_DELAY_MINUTES": event.arrival_delay_minutes,
        "DEPARTURE_DELAY_MINUTES": event.departure_delay_minutes,
        "STATUS": event.status,
        "SOURCE_NAME": event.source_name,
        "SOURCE_RECORD_HASH": _source_record_hash(raw),
        "SOURCE_OBSERVED_AT": None,
        "RUN_ID": run_id,
        "SOURCE_SCHEDULED_ARRIVAL_TIME": _value_as_str(raw.get("source_scheduled_arrival_time")),
        "SOURCE_ACTUAL_ARRIVAL_TIME": _value_as_str(raw.get("source_actual_arrival_time")),
        "SOURCE_SCHEDULED_DEPARTURE_TIME": _value_as_str(raw.get("source_scheduled_departure_time")),
        "SOURCE_ACTUAL_DEPARTURE_TIME": _value_as_str(raw.get("source_actual_departure_time")),
    }


def _chunks(rows: Iterator[dict[str, Any]], size: int) -> Iterator[list[dict[str, Any]]]:
    batch: list[dict[str, Any]] = []
    for row in rows:
        batch.append(row)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def _stage_sql() -> str:
    return f"CREATE OR REPLACE TEMPORARY TABLE {STAGE_TABLE} LIKE {RAW_TABLE}"


def _deduplicated_stage_relation() -> str:
    return (
        f"(SELECT * FROM {STAGE_TABLE} "
        "QUALIFY ROW_NUMBER() OVER (PARTITION BY SOURCE_RECORD_HASH ORDER BY TRAIN_NUMBER, JOURNEY_DATE, STATION_SEQUENCE) = 1)"
    )


def _write_chunk(connection: SnowflakeConnection, rows: list[dict[str, Any]]) -> None:
    dataframe = pd.DataFrame(rows)
    success, _chunks_count, _rows_count, output = write_pandas(
        connection,
        dataframe,
        STAGE_TABLE,
        quote_identifiers=False,
        auto_create_table=False,
    )
    if not success:
        raise RuntimeError(f"Snowflake bulk upload failed: {output}")


def load_rstgcn(
    connection: SnowflakeConnection,
    *,
    delay_path: Path,
    route_path: Path,
    quarantine_path: Path,
    chunk_size: int = 25_000,
) -> LoadResult:
    """Load RSTGCN data with validation, quarantine, deduplication, and audit rows.

    The function never downloads source data.  It reads the locally acquired,
    approved CSV files only and is safe to re-run: the source-record hash is
    used as the merge key.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    run_id = str(uuid.uuid4())
    received = valid = rejected = 0
    quarantine_path.parent.mkdir(parents=True, exist_ok=True)

    cursor = connection.cursor()
    try:
        # Temporary tables require session context; fully qualified target names
        # alone do not satisfy this Snowflake requirement.
        cursor.execute(f"USE DATABASE {RAW_DATABASE}")
        cursor.execute(f"USE SCHEMA {RAW_SCHEMA}")
        # Keep the loader deployable when the versioned migration has not yet
        # been run by the setup runner. ADD COLUMN IF NOT EXISTS is idempotent.
        for migration in SOURCE_TIME_MIGRATIONS:
            cursor.execute(migration)
        cursor.execute(
            f"""
            INSERT INTO {AUDIT_TABLE}
                (RUN_ID, PIPELINE_NAME, DATASET, SOURCE_NAME, STARTED_AT, STATUS)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP(), %s)
            """,
            (run_id, "railway_pipeline", "train_running_events", "rstgcn_sep2024", "running"),
        )
        cursor.execute(_stage_sql())

        def validated_rows() -> Iterator[dict[str, Any]]:
            nonlocal received, valid, rejected
            with quarantine_path.open("w", encoding="utf-8") as quarantine_file:
                for raw in _iter_rstgcn_records(delay_path=delay_path, route_path=route_path):
                    received += 1
                    try:
                        event = TrainRunningEvent.model_validate(raw)
                    except ValidationError as exc:
                        rejected += 1
                        quarantine_file.write(
                            json.dumps({"record": raw, "errors": exc.errors()}, default=str) + "\n"
                        )
                        continue
                    valid += 1
                    yield _warehouse_row(event, raw, run_id)

        for batch in _chunks(validated_rows(), chunk_size):
            _write_chunk(connection, batch)

        deduplicated = _deduplicated_stage_relation()
        cursor.execute(f"SELECT COUNT(*) FROM {deduplicated}")
        distinct_valid = int(cursor.fetchone()[0])
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM {deduplicated} source
            INNER JOIN {RAW_TABLE} target
                ON target.SOURCE_RECORD_HASH = source.SOURCE_RECORD_HASH
            """
        )
        already_present = int(cursor.fetchone()[0])
        cursor.execute(
            f"""
            MERGE INTO {RAW_TABLE} target
            USING {deduplicated} source
              ON target.SOURCE_RECORD_HASH = source.SOURCE_RECORD_HASH
            WHEN NOT MATCHED THEN INSERT (
                TRAIN_NUMBER, JOURNEY_DATE, STATION_CODE, STATION_SEQUENCE,
                SCHEDULED_ARRIVAL_AT, ACTUAL_ARRIVAL_AT,
                SCHEDULED_DEPARTURE_AT, ACTUAL_DEPARTURE_AT,
                ARRIVAL_DELAY_MINUTES, DEPARTURE_DELAY_MINUTES, STATUS,
                SOURCE_NAME, SOURCE_RECORD_HASH, SOURCE_OBSERVED_AT, RUN_ID,
                SOURCE_SCHEDULED_ARRIVAL_TIME, SOURCE_ACTUAL_ARRIVAL_TIME,
                SOURCE_SCHEDULED_DEPARTURE_TIME, SOURCE_ACTUAL_DEPARTURE_TIME
            ) VALUES (
                source.TRAIN_NUMBER, source.JOURNEY_DATE, source.STATION_CODE, source.STATION_SEQUENCE,
                source.SCHEDULED_ARRIVAL_AT, source.ACTUAL_ARRIVAL_AT,
                source.SCHEDULED_DEPARTURE_AT, source.ACTUAL_DEPARTURE_AT,
                source.ARRIVAL_DELAY_MINUTES, source.DEPARTURE_DELAY_MINUTES, source.STATUS,
                source.SOURCE_NAME, source.SOURCE_RECORD_HASH, source.SOURCE_OBSERVED_AT, source.RUN_ID,
                source.SOURCE_SCHEDULED_ARRIVAL_TIME, source.SOURCE_ACTUAL_ARRIVAL_TIME,
                source.SOURCE_SCHEDULED_DEPARTURE_TIME, source.SOURCE_ACTUAL_DEPARTURE_TIME
            )
            """
        )
        inserted = distinct_valid - already_present
        cursor.execute(
            f"""
            UPDATE {AUDIT_TABLE}
            SET COMPLETED_AT = CURRENT_TIMESTAMP(), RECORDS_RECEIVED = %s,
                RECORDS_INSERTED = %s, RECORDS_REJECTED = %s, STATUS = %s
            WHERE RUN_ID = %s
            """,
            (received, inserted, rejected, "succeeded", run_id),
        )
        connection.commit()
        return LoadResult(run_id, received, valid, rejected, distinct_valid, inserted, already_present, quarantine_path)
    except Exception:
        connection.rollback()
        cursor.execute(
            f"""
            UPDATE {AUDIT_TABLE}
            SET COMPLETED_AT = CURRENT_TIMESTAMP(), RECORDS_RECEIVED = %s,
                RECORDS_REJECTED = %s, STATUS = %s
            WHERE RUN_ID = %s
            """,
            (received, rejected, "failed", run_id),
        )
        connection.commit()
        raise
    finally:
        cursor.close()
