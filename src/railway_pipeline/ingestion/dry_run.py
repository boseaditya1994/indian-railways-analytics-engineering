"""Offline ingestion planning that validates provenance before any warehouse write."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from railway_pipeline.ingestion.file_adapter import read_running_event_csv
from railway_pipeline.ingestion.normalization import normalize_running_events
from railway_pipeline.ingestion.provenance import SourceProvenance


@dataclass(frozen=True)
class IngestionDryRun:
    accepted_count: int
    rejected_count: int


def validate_historical_file(path: Path, provenance: SourceProvenance) -> IngestionDryRun:
    """Validate an approved source locally; this function never loads Snowflake."""
    provenance.assert_ingestible()
    if not path.is_file():
        raise FileNotFoundError(path)
    normalized = normalize_running_events(read_running_event_csv(path, provenance.source_name))
    return IngestionDryRun(len(normalized.accepted), len(normalized.rejected))
