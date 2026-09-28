from datetime import date
from pathlib import Path

import pytest

from railway_pipeline.__main__ import build_parser


def test_backfill_requires_start_date() -> None:
    args = build_parser().parse_args(["--mode", "backfill"])
    assert args.start_date is None


def test_parser_accepts_iso_date() -> None:
    args = build_parser().parse_args(["--mode", "daily", "--start-date", "2024-01-01"])
    assert args.start_date == date(2024, 1, 1)


def test_invalid_mode_is_rejected() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--mode", "streaming"])


def test_cli_requires_input_and_provenance_together(tmp_path: Path) -> None:
    args = build_parser().parse_args(["--mode", "daily", "--input-path", str(tmp_path / "events.csv")])
    assert args.provenance_path is None
