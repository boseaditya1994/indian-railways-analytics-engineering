"""Adapter for the authors' documented RSTGCN September-2024 CSV layout.

This module contains no downloader. It may be used only after the dataset's reuse
permission is recorded in a provenance manifest.
"""

from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path

DELAY_COLUMNS = {"train", "date", "station", "sch_arr", "act_arr", "arr_delay", "sch_dep", "act_dep", "dep_delay"}
ROUTE_COLUMNS = {"stnSerialNumber", "trainNumber", "station_code"}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _headers(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return set(csv.DictReader(handle).fieldnames or [])


def _iter_csv(path: Path) -> Iterator[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        yield from csv.DictReader(handle)


def read_rstgcn_events(delay_path: Path, route_path: Path, source_name: str = "rstgcn_sep2024") -> Iterator[dict[str, str | float | int | None]]:
    """Join RSTGCN delay records to route sequences at train/date/station grain."""
    route_rows = _read_csv(route_path)
    delay_headers = _headers(delay_path)
    route_headers = _headers(route_path)
    if missing := DELAY_COLUMNS - delay_headers:
        raise ValueError(f"RSTGCN delay file missing columns: {', '.join(sorted(missing))}")
    if missing := ROUTE_COLUMNS - route_headers:
        raise ValueError(f"RSTGCN route file missing columns: {', '.join(sorted(missing))}")

    sequence = {
        (row["trainNumber"].strip(), row["station_code"].strip().upper()): int(row["stnSerialNumber"])
        for row in route_rows
    }
    for row in _iter_csv(delay_path):
        train_number = row["train"].strip()
        station_code = row["station"].strip().upper()
        station_sequence = sequence.get((train_number, station_code))
        if station_sequence is None:
            # Preserve the source observation for quarantine rather than inventing a sequence.
            yield {
                "train_number": train_number,
                "journey_date": row["date"],
                "station_code": station_code,
                "station_sequence": 0,
                "source_name": source_name,
                "arrival_delay_minutes": _number_or_none(row["arr_delay"]),
                "departure_delay_minutes": _number_or_none(row["dep_delay"]),
                "source_scheduled_arrival_time": row["sch_arr"],
                "source_actual_arrival_time": row["act_arr"],
                "source_scheduled_departure_time": row["sch_dep"],
                "source_actual_departure_time": row["act_dep"],
            }
            continue
        yield {
            "train_number": train_number,
            "journey_date": row["date"],
            "station_code": station_code,
            "station_sequence": station_sequence,
            "source_name": source_name,
            "arrival_delay_minutes": _number_or_none(row["arr_delay"]),
            "departure_delay_minutes": _number_or_none(row["dep_delay"]),
            "source_scheduled_arrival_time": row["sch_arr"],
            "source_actual_arrival_time": row["act_arr"],
            "source_scheduled_departure_time": row["sch_dep"],
            "source_actual_departure_time": row["act_dep"],
        }


def _number_or_none(value: str | None) -> float | None:
    return None if value in (None, "") else float(value)
