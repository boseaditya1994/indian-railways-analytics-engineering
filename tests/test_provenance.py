from datetime import datetime

import pytest

from railway_pipeline.ingestion.provenance import SourceProvenance


def source(local_processing_permitted: bool) -> SourceProvenance:
    return SourceProvenance(
        source_name="licensed historical source",
        source_url="https://example.org/dataset",
        license_name="CC BY 4.0",
        retrieved_at=datetime(2025, 1, 1),
        coverage_description="Station-level historical journey delay observations.",
        local_processing_permitted=local_processing_permitted,
    )


def test_disallowed_source_cannot_be_processed() -> None:
    with pytest.raises(ValueError, match="not approved"):
        source(False).assert_ingestible()


def test_allowed_source_is_accepted() -> None:
    source(True).assert_ingestible()
