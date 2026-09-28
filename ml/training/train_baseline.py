"""Train/evaluate the required train-station historical mean baseline from approved CSV data."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, time
from pathlib import Path

from railway_pipeline.prediction.baseline import TrainRouteMeanBaseline
from railway_pipeline.prediction.evaluation import summarize_evaluation


def read_observations(path: Path) -> list[tuple[datetime, str, str, float]]:
    required = {"journey_date", "train_number", "station_code", "arrival_delay_minutes"}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"missing baseline fields: {', '.join(sorted(missing))}")
        observations: list[tuple[datetime, str, str, float]] = []
        for row in reader:
            if row["arrival_delay_minutes"] in (None, ""):
                continue
            observations.append(
                (
                    datetime.combine(date.fromisoformat(row["journey_date"]), time.min),
                    row["train_number"].upper(),
                    row["station_code"].upper(),
                    float(row["arrival_delay_minutes"]),
                )
            )
    if len(observations) < 10:
        raise ValueError("at least ten non-null historical delay observations are required")
    return sorted(observations, key=lambda observation: observation[0])


def train_and_evaluate(path: Path) -> dict[str, object]:
    observations = read_observations(path)
    split_index = max(1, int(len(observations) * 0.8))
    train, test = observations[:split_index], observations[split_index:]
    if not test:
        raise ValueError("historical file needs an untouched chronological test period")
    baseline = TrainRouteMeanBaseline().fit((train_no, station, delay) for _, train_no, station, delay in train)
    actual = [delay for _, _, _, delay in test]
    prediction = [baseline.predict(train_no, station) for _, train_no, station, _ in test]
    # The global mean provides a deliberately weaker reference baseline.
    reference = [baseline.global_mean] * len(test)
    evaluation = summarize_evaluation("train_station_historical_mean", actual, prediction, reference)
    return {
        "model_name": evaluation.model_name,
        "train_rows": len(train),
        "test_rows": len(test),
        "mae": evaluation.mae,
        "rmse": evaluation.rmse,
        "global_mean_mae": evaluation.baseline_mae,
        "improves_on_global_mean": evaluation.improves_on_baseline,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-path", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    args = parser.parse_args()
    metrics = train_and_evaluate(args.input_path)
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
