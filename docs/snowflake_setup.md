# Snowflake setup

After the read-only preflight succeeds, run:

```powershell
.\.venv\Scripts\python.exe .\scripts\snowflake_setup.py
```

The runner executes version-controlled DDL for `RAIL_DELAY_ANALYTICS`, its schemas, RAW
tables, audit tables, and ML prediction tables. It uses the existing `COMPUTE_WH` and
does not create or alter warehouses. Enter the password only into the hidden local prompt.
