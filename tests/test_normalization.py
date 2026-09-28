from railway_pipeline.ingestion.normalization import normalize_running_events


def valid_record() -> dict[str, object]:
    return {
        "train_number": "12345",
        "journey_date": "2024-01-01",
        "station_code": "hwh",
        "station_sequence": 2,
        "source_name": "licensed_historical_file",
        "arrival_delay_minutes": None,
    }


def test_normalization_standardizes_identifiers_and_preserves_null_delay() -> None:
    result = normalize_running_events([valid_record()])
    assert result.accepted[0]["station_code"] == "HWH"
    assert result.accepted[0]["arrival_delay_minutes"] is None


def test_normalization_deduplicates_exact_raw_records() -> None:
    result = normalize_running_events([valid_record(), valid_record()])
    assert len(result.accepted) == 1


def test_normalization_quarantines_invalid_records() -> None:
    invalid = valid_record() | {"station_sequence": 0}
    result = normalize_running_events([invalid])
    assert not result.accepted
    assert len(result.rejected) == 1
