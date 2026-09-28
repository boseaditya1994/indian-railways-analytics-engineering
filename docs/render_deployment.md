# Public dashboard API deployment

The GitHub Pages dashboard is static. Render hosts the separate FastAPI service so the browser never receives Snowflake credentials.

## One-time Snowflake setup

Run [004_dashboard_reader.sql](../snowflake/setup/004_dashboard_reader.sql) as `ACCOUNTADMIN`. Then create a dedicated Snowflake service user, grant it `RAIL_DELAY_DASHBOARD_READER`, and set a strong password. This role has only warehouse usage and the four objects queried by the dashboard.

## Render setup

1. Sign in to Render with GitHub and select **New → Blueprint** for this repository. Render will read `render.yaml` and create the free web service.
2. In the Render service's Environment page, set these secret variables: `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, and `SNOWFLAKE_PASSWORD`. Use the dedicated reader user, not `ACCOUNTADMIN`.
3. Deploy, then confirm `https://<service>.onrender.com/health` returns `{"status":"ok"}`.
4. Add the service URL (without a trailing slash) as the repository Actions variable `DASHBOARD_API_BASE_URL`, then rerun **Deploy portfolio dashboard**. The Pages build will use the hosted API.

`RAILRADAR_API_KEY` is deliberately not configured in the public service. RailRadar granted personal sandbox use; putting it behind an unauthenticated public endpoint would let arbitrary visitors consume that personal quota. Local live lookups remain available through `.env`.

## Rotation and incident response

Rotate the dedicated Snowflake password in Snowsight and then update the Render secret. If the hosted API behaves unexpectedly, suspend the Render service or revoke the service user's role; neither action affects the local pipeline account.
