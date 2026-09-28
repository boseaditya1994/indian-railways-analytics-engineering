from pathlib import Path

from ml.training.train_baseline import train_and_evaluate


def test_baseline_training_uses_chronological_holdout(tmp_path: Path) -> None:
    source = tmp_path / "history.csv"
    rows = ["journey_date,train_number,station_code,arrival_delay_minutes"]
    rows.extend(f"2024-01-{day:02d},12345,HWH,{day}" for day in range(1, 13))
    source.write_text("\n".join(rows), encoding="utf-8")
    metrics = train_and_evaluate(source)
    assert metrics["train_rows"] == 9
    assert metrics["test_rows"] == 3
    assert "mae" in metrics
