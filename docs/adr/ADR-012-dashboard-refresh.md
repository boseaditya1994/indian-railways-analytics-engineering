# ADR-012: Dashboard refresh

## Decision

Refresh dashboard data only after a successful batch pipeline publishes marts or an API
response. The initial dashboard does not promise automatic hosted refresh.

## Consequences

Refresh claims remain verifiable and match the deployed architecture.
