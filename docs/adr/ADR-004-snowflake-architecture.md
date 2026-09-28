# ADR-004: Snowflake architecture

## Context

The portfolio workload needs reproducible storage and transformations while controlling
cost and preserving source lineage.

## Options

1. One schema with direct-overwrite tables.
2. Layered schemas with immutable raw records and dbt transformations.

## Decision

Use `RAW`, `STAGING`, `INTERMEDIATE`, `MARTS`, `FEATURES`, `ML`, and `AUDIT` schemas.
Use the account-managed `COMPUTE_WH` and do not create or change warehouse settings from
project code.

## Consequences

The platform supports replay, auditability, incremental transforms, and cost control.
Account-level object creation remains an explicit, reviewed step.
