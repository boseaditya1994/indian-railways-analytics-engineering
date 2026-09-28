# RailRadar prospective live archive

This is a separate personal-portfolio source, not a replacement for the approved RSTGCN September 2024 history. It stores normalized live snapshots only after the archive begins; it does not backfill arbitrary dates.

Set `RAILRADAR_API_KEY` only in the ignored local `.env` file. Run a manual archival snapshot for an explicit, small watchlist:

```powershell
.\.venv\Scripts\python.exe .\scripts\archive_raildar_live_status.py --train 12919 --train 12301
```

The Sandbox allows 1,000 requests/month. A five-train watchlist twice daily uses roughly 300 requests/month, leaving capacity for manual dashboard lookups. Do not schedule it until the watchlist and cadence are deliberately chosen.
