"""Read-only post-load reconciliation for the approved RSTGCN load."""

from __future__ import annotations

import getpass
import sys

import snowflake.connector

from railway_pipeline.config.settings import Settings


def _scalar(cursor: object, query: str) -> object:
    cursor.execute(query)  # type: ignore[attr-defined]
    return cursor.fetchone()[0]  # type: ignore[attr-defined]


def main() -> None:
    settings = Settings()
    password = getpass.getpass("Snowflake password (not saved): ")
    connection = snowflake.connector.connect(
        account=settings.snowflake_account,
        user=settings.snowflake_user,
        password=password,
        role=settings.snowflake_role,
        warehouse=settings.snowflake_warehouse,
        database=settings.snowflake_database,
    )
    try:
        cursor = connection.cursor()
        try:
            raw_count = _scalar(
                cursor,
                "SELECT COUNT(*) FROM RAIL_DELAY_ANALYTICS.RAW.TRAIN_RUNNING_EVENTS "
                "WHERE SOURCE_NAME = 'rstgcn_sep2024'",
            )
            hash_count = _scalar(
                cursor,
                "SELECT COUNT(DISTINCT SOURCE_RECORD_HASH) FROM RAIL_DELAY_ANALYTICS.RAW.TRAIN_RUNNING_EVENTS "
                "WHERE SOURCE_NAME = 'rstgcn_sep2024'",
            )
            date_min = _scalar(
                cursor,
                "SELECT MIN(JOURNEY_DATE) FROM RAIL_DELAY_ANALYTICS.RAW.TRAIN_RUNNING_EVENTS "
                "WHERE SOURCE_NAME = 'rstgcn_sep2024'",
            )
            date_max = _scalar(
                cursor,
                "SELECT MAX(JOURNEY_DATE) FROM RAIL_DELAY_ANALYTICS.RAW.TRAIN_RUNNING_EVENTS "
                "WHERE SOURCE_NAME = 'rstgcn_sep2024'",
            )
            cursor.execute(
                """
                SELECT RUN_ID, RECORDS_RECEIVED, RECORDS_INSERTED, RECORDS_REJECTED, STATUS
                FROM RAIL_DELAY_ANALYTICS.AUDIT.INGESTION_RUN_AUDIT
                WHERE DATASET = 'train_running_events' AND SOURCE_NAME = 'rstgcn_sep2024'
                ORDER BY STARTED_AT DESC
                LIMIT 1
                """
            )
            latest_run = cursor.fetchone()
        finally:
            cursor.close()
    finally:
        connection.close()

    print("Snowflake reconciliation succeeded")
    print(f"RSTGCN raw rows: {raw_count}")
    print(f"Distinct source hashes: {hash_count}")
    print(f"Journey date range: {date_min} to {date_max}")
    if latest_run:
        print("Latest audit run: " + " | ".join(str(value) for value in latest_run))
    if raw_count != hash_count:
        raise RuntimeError("Reconciliation failed: duplicate source hashes exist in the raw table")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Snowflake reconciliation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
