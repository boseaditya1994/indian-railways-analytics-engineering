from datetime import datetime

import pytest

from railway_pipeline.ingestion.watermark import extraction_start


def test_initial_backfill_has_no_watermark() -> None:
    assert extraction_start(None) is None


def test_overlap_re_reads_recent_records() -> None:
    watermark = datetime(2025, 1, 3, 12, 0)
    assert extraction_start(watermark, overlap_hours=48) == datetime(2025, 1, 1, 12, 0)


def test_negative_overlap_is_invalid() -> None:
    with pytest.raises(ValueError):
        extraction_start(datetime(2025, 1, 1), overlap_hours=-1)
