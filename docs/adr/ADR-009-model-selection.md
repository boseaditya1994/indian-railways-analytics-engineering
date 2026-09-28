# ADR-009: Model selection

## Decision

Start with the train-station historical mean baseline. Evaluate a simple regularized or
tree-based candidate only if it can beat the baseline on a final chronological holdout.

## Consequences

Complexity is earned through measured improvement, not résumé keyword stuffing.
