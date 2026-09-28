"""Validate source payloads and isolate rejected records without silent data loss."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from railway_pipeline.models.running_event import TrainRunningEvent
from railway_pipeline.utils.hashing import source_record_hash


@dataclass
class NormalizationResult:
    accepted: list[dict[str, Any]] = field(default_factory=list)
    rejected: list[dict[str, Any]] = field(default_factory=list)


def normalize_running_events(records: Iterable[dict[str, Any]]) -> NormalizationResult:
    """Return canonical records plus auditable rejections; never coerce null delays to zero."""
    result = NormalizationResult()
    seen_hashes: set[str] = set()
    for raw in records:
        record_hash = source_record_hash(raw)
        if record_hash in seen_hashes:
            continue
        seen_hashes.add(record_hash)
        try:
            event = TrainRunningEvent.model_validate(raw)
        except ValidationError as error:
            result.rejected.append({"raw_record": raw, "error": str(error), "source_record_hash": record_hash})
            continue
        accepted = event.model_dump(mode="json")
        accepted["source_record_hash"] = record_hash
        result.accepted.append(accepted)
    return result
