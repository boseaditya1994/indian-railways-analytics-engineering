"""Run-level audit records used by loaders and reconciliation."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class IngestionRunAudit(BaseModel):
    run_id: UUID = Field(default_factory=uuid4)
    pipeline_name: str
    dataset: str
    source_name: str
    started_at: datetime
    watermark_at: datetime | None = None
    completed_at: datetime | None = None
    records_received: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    records_rejected: int = 0
    status: str = "started"
    error_message: str | None = None
