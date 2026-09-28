# Warehouse validation and dbt

After a successful RSTGCN load, run the read-only reconciliation report:

```powershell
.\.venv\Scripts\python.exe .\scripts\snowflake_reconcile.py
```

It confirms source row count, source-hash uniqueness, journey-date coverage, and the newest ingestion-audit record. It makes no Snowflake changes.

The dbt project uses a project-local profile and loads non-secret account settings from the ignored `.env` file. `run_dbt.ps1` prompts for the password as a PowerShell secure string, exposes it only to the child dbt process, then removes it.

The development profile uses one dbt worker. This avoids concurrent schema-initialisation requests against the shared `ANALYTICS` schema, which can otherwise trigger an intermittent Snowflake internal error. Increase threads only after moving production runs to an isolated deployment schema.

```powershell
.\scripts\run_dbt.ps1 debug
.\scripts\run_dbt.ps1 build
```

Run `debug` first. Only run `build` after it succeeds; dbt will create or refresh the project models in the configured `ANALYTICS` schema.
