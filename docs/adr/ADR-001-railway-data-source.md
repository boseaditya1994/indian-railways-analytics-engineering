# ADR-001: Railway data source

## Context

No official public developer API for automated nationwide historical running-status
ingestion was validated during Phase 0.

## Options

1. Scrape passenger-facing railway services.
2. Use a clearly licensed historical dataset and optional authorized third-party API.
3. Fabricate/simulate historical data.

## Decision

Choose option 2. Do not use options 1 or 3.

## Consequences

The MVP is scoped to verified coverage rather than claiming national real-time service.
