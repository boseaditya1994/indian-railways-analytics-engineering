import json
from pathlib import Path


def test_synthetic_fixture_is_explicitly_labelled() -> None:
    fixture = Path(__file__).parent / "fixtures" / "synthetic_train_running_events.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    assert payload["fixture_type"] == "synthetic_test_data_only"
    assert payload["records"][0]["source_name"] == "synthetic_test_fixture"
