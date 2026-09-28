from pathlib import Path

import pytest

from railway_pipeline.ingestion.file_adapter import read_running_event_csv


def test_file_adapter_reads_contract_columns(tmp_path: Path) -> None:
    source = tmp_path / "events.csv"
    source.write_text("train_number,journey_date,station_code,station_sequence\n12345,2024-01-01,HWH,1\n")
    assert list(read_running_event_csv(source, "approved_file"))[0]["source_name"] == "approved_file"


def test_file_adapter_rejects_missing_contract_columns(tmp_path: Path) -> None:
    source = tmp_path / "events.csv"
    source.write_text("train_number,journey_date\n12345,2024-01-01\n")
    with pytest.raises(ValueError, match="station_code"):
        list(read_running_event_csv(source, "approved_file"))
