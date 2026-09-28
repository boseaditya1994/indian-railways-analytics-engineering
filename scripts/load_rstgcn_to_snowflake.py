"""Load the locally acquired, approved RSTGCN data into Snowflake."""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

import snowflake.connector

from railway_pipeline.config.settings import Settings
from railway_pipeline.loaders.rstgcn_loader import load_rstgcn


ROOT = Path(__file__).resolve().parents[1]


def _find_one(directory: Path, pattern: str) -> Path:
    matches = list(directory.rglob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one {pattern} beneath {directory}; found {len(matches)}")
    return matches[0]


def main() -> None:
    settings = Settings()
    source_dir = ROOT / "data" / "raw" / "rstgcn_sep2024"
    delay_path = _find_one(source_dir, "train_routes_delays_Sep2024.csv")
    route_path = _find_one(source_dir, "train_routes_Sep2024.csv")
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
        result = load_rstgcn(
            connection,
            delay_path=delay_path,
            route_path=route_path,
            quarantine_path=ROOT / "artifacts" / "quality" / "rstgcn_sep2024_load_quarantine.jsonl",
        )
    finally:
        connection.close()

    print("RSTGCN Snowflake load succeeded")
    print(f"Run ID: {result.run_id}")
    print(f"Records received: {result.received}")
    print(f"Records valid: {result.valid}")
    print(f"Records rejected: {result.rejected}")
    print(f"Distinct valid records: {result.distinct_valid}")
    print(f"Inserted: {result.inserted}")
    print(f"Already present: {result.already_present}")
    print(f"Quarantine file: {result.quarantine_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"RSTGCN Snowflake load failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
