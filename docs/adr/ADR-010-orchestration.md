# ADR-010: Orchestration

## Decision

Use GitHub Actions for CI and opt-in scheduled batch orchestration in the MVP.

## Consequences

The workflow remains inexpensive and reproducible; it does not run until secrets and an
approved source adapter are configured.
