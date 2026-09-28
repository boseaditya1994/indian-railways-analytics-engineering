# ADR-008: Prediction target

## Context

The source coverage is expected to be station-stop observations over historical journeys.

## Options

1. Predict final journey delay only.
2. Predict arrival delay at the next target stop from information available before it.

## Decision

Use arrival delay in minutes at the next planned target station as the MVP regression
target. Store prediction timestamp and target station in every prediction result.

## Consequences

Previous-station delay is valid only after that station has been observed. Historical
aggregates must exclude the current journey's future target outcome.
