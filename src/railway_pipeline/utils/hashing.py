"""Stable record hashing for idempotent raw ingestion."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def source_record_hash(record: dict[str, Any]) -> str:
    """Hash a record canonically, independent of source field ordering."""
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
