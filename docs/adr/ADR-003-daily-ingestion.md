# ADR-003: Daily ingestion

## Decision

Use scheduled batch ingestion with a 48-hour re-read window and source watermark.

## Consequences

This correctly describes mutable daily records without claiming real-time streaming.
