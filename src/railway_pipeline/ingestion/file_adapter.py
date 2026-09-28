"""CSV adapter for an approved historical source file; no network retrieval occurs here."""

from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = {"train_number", "journey_date", "station_code", "station_sequence"}


def read_running_event_csv(path: Path, source_name: str) -> Iterator[dict[str, Any]]:
    """Yield source rows after checking the minimum station-stop contract columns."""
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - headers
        if missing:
            raise ValueError(f"historical file is missing required columns: {', '.join(sorted(missing))}")
        for row in reader:
            yield {**row, "source_name": source_name}
