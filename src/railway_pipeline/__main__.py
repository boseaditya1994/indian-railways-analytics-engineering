"""Command-line entry point for local pipeline orchestration."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from railway_pipeline.ingestion.dry_run import validate_historical_file
from railway_pipeline.ingestion.normalization import normalize_running_events
from railway_pipeline.ingestion.provenance import SourceProvenance
from railway_pipeline.ingestion.rstgcn_adapter import read_rstgcn_events


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Indian Railways data pipeline")
    parser.add_argument("--mode", choices=("backfill", "daily"), required=True)
    parser.add_argument("--start-date", type=date.fromisoformat)
    parser.add_argument("--end-date", type=date.fromisoformat)
    parser.add_argument("--input-path", type=Path, help="Approved historical CSV for local preflight")
    parser.add_argument("--rstgcn-delay-path", type=Path, help="RSTGCN train_routes_delays_Sep2024.csv")
    parser.add_argument("--rstgcn-route-path", type=Path, help="RSTGCN train_routes_Sep2024.csv")
    parser.add_argument("--provenance-path", type=Path, help="JSON provenance manifest for --input-path")
    parser.add_argument("--quarantine-report-path", type=Path, help="Optional JSON report for rejected source records")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.mode == "backfill" and args.start_date is None:
        raise SystemExit("--start-date is required for backfill mode")
    if args.end_date and args.start_date and args.end_date < args.start_date:
        raise SystemExit("--end-date must not precede --start-date")
    rstgcn_requested = bool(args.rstgcn_delay_path) or bool(args.rstgcn_route_path)
    if args.input_path and rstgcn_requested:
        raise SystemExit("choose either --input-path or the two RSTGCN paths")
    if bool(args.rstgcn_delay_path) != bool(args.rstgcn_route_path):
        raise SystemExit("--rstgcn-delay-path and --rstgcn-route-path must be supplied together")
    if bool(args.input_path or rstgcn_requested) != bool(args.provenance_path):
        raise SystemExit("a source input and --provenance-path must be supplied together")
    if args.input_path:
        provenance = SourceProvenance.model_validate_json(args.provenance_path.read_text(encoding="utf-8-sig"))
        result = validate_historical_file(args.input_path, provenance)
        print(f"Historical preflight passed: {result.accepted_count} accepted, {result.rejected_count} rejected.")
        return
    if rstgcn_requested:
        provenance = SourceProvenance.model_validate_json(args.provenance_path.read_text(encoding="utf-8-sig"))
        provenance.assert_ingestible()
        normalized = normalize_running_events(read_rstgcn_events(args.rstgcn_delay_path, args.rstgcn_route_path))
        if args.quarantine_report_path:
            args.quarantine_report_path.parent.mkdir(parents=True, exist_ok=True)
            args.quarantine_report_path.write_text(json.dumps(normalized.rejected, indent=2), encoding="utf-8")
        print(f"RSTGCN preflight passed: {len(normalized.accepted)} accepted, {len(normalized.rejected)} rejected.")
        return
    print(f"Pipeline mode '{args.mode}' validated. No ingestion adapter has run.")


if __name__ == "__main__":
    main()
