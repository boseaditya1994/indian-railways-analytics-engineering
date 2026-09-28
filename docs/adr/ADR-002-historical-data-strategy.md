# ADR-002: Historical data strategy

## Context

Station-level historical actual times are not available through a verified official public
developer API.

## Decision

Accept only a source with documented provenance and reuse permission. Use a local
preflight before warehouse loading. Do not substitute synthetic data for real performance.

## Consequences

Model execution waits for approved data; source limits are visible in the portfolio.
