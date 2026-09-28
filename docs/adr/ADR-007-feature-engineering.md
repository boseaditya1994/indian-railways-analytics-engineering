# ADR-007: Feature engineering

## Decision

Generate features from information known at or before prediction time; reject later source
observations via the leakage guard.

## Consequences

Historical metrics more closely represent deployable prediction behavior.
