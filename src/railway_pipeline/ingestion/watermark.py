"""Pure functions for safe incremental extraction windows."""

from datetime import datetime, timedelta


def extraction_start(last_successful_watermark: datetime | None, overlap_hours: int = 48) -> datetime | None:
    """Return a re-read window to capture late corrections without full reloads."""
    if overlap_hours < 0:
        raise ValueError("overlap_hours must be non-negative")
    if last_successful_watermark is None:
        return None
    return last_successful_watermark - timedelta(hours=overlap_hours)
