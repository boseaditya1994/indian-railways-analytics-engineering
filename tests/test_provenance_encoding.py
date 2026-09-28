from datetime import datetime
from pathlib import Path

from railway_pipeline.ingestion.provenance import SourceProvenance


def test_provenance_manifest_accepts_utf8_bom(tmp_path: Path) -> None:
    manifest = tmp_path / "provenance.json"
    manifest.write_text(
        '{"source_name":"approved source","source_url":"https://example.org/data",'
        '"license_name":"CC BY 4.0","retrieved_at":"2025-01-01T00:00:00Z",'
        '"coverage_description":"Station-level delay observations for testing.",'
        '"local_processing_permitted":true}',
        encoding="utf-8-sig",
    )
    source = SourceProvenance.model_validate_json(manifest.read_text(encoding="utf-8-sig"))
    assert source.retrieved_at == datetime(2025, 1, 1, 0, 0, tzinfo=source.retrieved_at.tzinfo)
