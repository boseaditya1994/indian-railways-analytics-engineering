# RailRadar prospective live archive

This is a separate personal-portfolio source, not a replacement for the approved RSTGCN September 2024 history. It stores normalized live snapshots only after the archive begins; it does not backfill arbitrary dates.

Set `RAILRADAR_API_KEY` only in the ignored local `.env` file. The Snowflake password is stored separately in Windows Credential Manager for the current Windows user.

## Data-driven watchlist and scheduling

The scheduled archive selects the five train numbers with the most September 2024 observations in the approved RSTGCN fact mart. It runs at 8:00 AM and 8:00 PM local time while the user is logged in.

Run this once from PowerShell in the repository root. It securely prompts for the Snowflake password, stores it in Windows Credential Manager, and creates the scheduled task; no password is written to the repository, `.env`, task command, or logs.

```powershell
.\scripts\setup_raildar_archive.ps1
```

To test the exact same watchlist immediately after setup:

```powershell
.\scripts\run_raildar_archive.ps1
```

For a one-off explicit small watchlist, use:

```powershell
.\.venv\Scripts\python.exe .\scripts\archive_raildar_live_status.py --train 12919 --train 12301
```

The Sandbox allows 1,000 requests/month. A five-train watchlist twice daily uses roughly 300 requests/month, leaving capacity for manual dashboard lookups. This remains a prospective source only and never changes the separate RSTGCN September 2024 history.
