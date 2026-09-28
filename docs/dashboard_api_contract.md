# Dashboard API contract

The React application must call a server-side API. It must never connect directly to
Snowflake or include account names, credentials, private keys, or tokens in browser code.

## Initial endpoints

| Endpoint | Response purpose |
| --- | --- |
| `GET /health` | Service liveness only |
| `GET /v1/dashboard/network-overview` | Aggregated network KPIs |
| `GET /v1/dashboard/pipeline-health` | Freshness and ingestion-health summary |

Until a successful approved-source pipeline run exists, endpoints return a visible
`awaiting_approved_source` status and null metrics. This is intentional.

The production repository implementation will query only analytics/audit marts through a
least-privilege Snowflake role. The API owns all warehouse access.
