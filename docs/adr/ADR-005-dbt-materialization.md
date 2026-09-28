# ADR-005: dbt materialization

## Decision

Use views for staging/intermediate transformations, tables for dimensions/marts, and merge
incremental materialization for large facts and features.

## Consequences

Reruns remain idempotent while warehouse compute is controlled.
