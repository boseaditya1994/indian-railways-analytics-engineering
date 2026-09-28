# Historical backfill preflight

The first historical run is intentionally two-stage:

1. Create a provenance manifest from `data/provenance/source_manifest.example.json`.
2. Run the local validation preflight before a warehouse load.

```powershell
railway-pipeline --mode backfill --start-date 2024-01-01 `
  --input-path data/raw/approved_history.csv `
  --provenance-path data/provenance/approved_history.json
```

The preflight validates source approval, required grain fields, identifier normalization,
exact duplicate payloads, and rejects invalid records into an auditable result. It does
not make a network request or write to Snowflake.
