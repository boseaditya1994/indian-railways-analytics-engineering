"""Reconciliation helpers that make row-loss visible between pipeline layers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReconciliationResult:
    source_count: int
    raw_count: int
    staging_count: int
    mart_count: int
    rejected_count: int
    duplicate_count: int

    @property
    def accounted_for(self) -> bool:
        return self.source_count == self.raw_count + self.rejected_count + self.duplicate_count

    @property
    def transformations_complete(self) -> bool:
        return self.staging_count >= self.mart_count


def reconcile(
    *,
    source_count: int,
    raw_count: int,
    staging_count: int,
    mart_count: int,
    rejected_count: int,
    duplicate_count: int,
) -> ReconciliationResult:
    """Build a transparent reconciliation result; validation occurs at the caller boundary."""
    counts = (source_count, raw_count, staging_count, mart_count, rejected_count, duplicate_count)
    if any(count < 0 for count in counts):
        raise ValueError("reconciliation counts cannot be negative")
    return ReconciliationResult(*counts)
