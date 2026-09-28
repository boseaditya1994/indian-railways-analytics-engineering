"""Required provenance metadata for every ingestible source asset."""

from __future__ import annotations

from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, Field


class SourceProvenance(BaseModel):
    source_name: str = Field(min_length=3)
    source_url: AnyHttpUrl
    license_name: str = Field(min_length=3)
    retrieved_at: datetime
    coverage_description: str = Field(min_length=10)
    local_processing_permitted: bool
    automated_access_permitted: bool = False
    raw_redistribution_permitted: bool = False

    def assert_ingestible(self) -> None:
        if not self.local_processing_permitted:
            raise ValueError("source is not approved for local processing")
