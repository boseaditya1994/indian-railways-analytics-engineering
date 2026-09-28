# RSTGCN → Snowflake load

This loader reads only the locally acquired, approved RSTGCN September 2024 CSVs. It does not download data and never stores a Snowflake password.

Load the files in 25,000-row chunks:

```powershell
.\.venv\Scripts\python.exe .\scripts\load_rstgcn_to_snowflake.py
```

The loader first applies its safe additive source-time migration, writes a run record to `RAIL_DELAY_ANALYTICS.AUDIT.INGESTION_RUN_AUDIT`, quarantines invalid records locally under `artifacts/quality/`, and merges on `SOURCE_RECORD_HASH`. Re-running it is safe: rows already in `RAW.TRAIN_RUNNING_EVENTS` are counted as `Already present` rather than inserted again.

Load the companion route/schedule file before running dbt. It is also idempotent:

```powershell
.\.venv\Scripts\python.exe .\scripts\load_rstgcn_schedule_to_snowflake.py
```

Original source time strings are retained as strings because the public source does not provide an unambiguous timestamp date/timezone for conversion. Timestamp fields intentionally remain null until a documented conversion rule is approved.
