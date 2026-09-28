# Dashboard API

The React dashboard consumes this API rather than connecting to Snowflake directly. The API exposes aggregate mart data only; browser code never receives Snowflake credentials.

Install the optional API dependencies once if needed:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dashboard,warehouse]"
```

Start the local API with a hidden password prompt:

```powershell
.\scripts\run_dashboard_api.ps1
```

In a second terminal, start the React dashboard. Vite proxies `/v1` to the local API during development:

```powershell
cd .\dashboards\react
npm install
npm run dev
```

Available endpoints:

- `GET http://127.0.0.1:8000/health`
- `GET http://127.0.0.1:8000/v1/dashboard/network-overview`
- `GET http://127.0.0.1:8000/v1/dashboard/pipeline-health`

Each response contains a `data_status` object. `ready` means metrics come from the approved RSTGCN September 2024 load; other states are intentionally non-misleading unavailable/configuration states.

The GitHub Pages deployment uses a committed aggregate-only static snapshot when no API is available. It is labeled `historical_snapshot` and intentionally omits live RailRadar lookups and all credentials.

## Optional RailRadar live snapshot

For personal, on-demand live lookup only, set `RAILRADAR_API_KEY` in the ignored local `.env` file and restart the API. The key is server-side only. This endpoint returns a compact current snapshot and does not save RailRadar responses in Snowflake or local files:

`GET http://127.0.0.1:8000/v1/live/trains/12919`

The API validates five-digit train numbers, caches an identical lookup for 30 seconds, and returns a clear `rate_limited` state if RailRadar returns HTTP 429. Do not use it for bulk polling or historical retention unless RailRadar explicitly approves that scope.
