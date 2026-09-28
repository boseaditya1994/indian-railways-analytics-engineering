# Data contract: `train_running_events`

## Grain

One observed train + journey date + station stop.

## Required fields

| Field | Rule |
| --- | --- |
| `train_number` | Non-empty normalized identifier |
| `journey_date` | ISO calendar date |
| `station_code` | Non-empty normalized station identifier |
| `station_sequence` | Positive integer; unmatched source records are quarantined |
| `source_name` | Registered provenance source |

## Optional observed fields

Scheduled/actual arrival/departure timestamps, delay minutes, source-observation time,
and status. Missing observed values remain null; they are never converted to zero.

## Idempotency and quality

Raw payload content receives a SHA-256 hash. Exact duplicates are skipped, invalid fields
are quarantined with the raw record/hash/error, and dbt resolves repeated natural keys by
latest ingestion time.
