# Data-quality results

## RSTGCN September 2024 initial preflight

| Metric | Measured value |
| --- | ---: |
| Accepted canonical station-stop records | 1,282,263 |
| Quarantined records | 62 |
| Rejected share | 0.0048% |

The preflight normalizes train/station identifiers, joins train delays to route sequences,
deduplicates exact raw payloads, and quarantines invalid records. The local quarantine
report will be written to `artifacts/quality/` on the next preflight run and is not
committed. Counts will be repeated after warehouse ingestion and dbt transformation as
part of reconciliation.
