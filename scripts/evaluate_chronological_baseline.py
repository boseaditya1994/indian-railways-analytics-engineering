"""Evaluate a leakage-safe train/station mean baseline directly in Snowflake."""

from __future__ import annotations

import getpass
import sys
import uuid

import snowflake.connector

from railway_pipeline.config.settings import Settings


def main() -> None:
    settings = Settings()
    password = getpass.getpass("Snowflake password (not saved): ")
    connection = snowflake.connector.connect(account=settings.snowflake_account, user=settings.snowflake_user, password=password, role=settings.snowflake_role, warehouse=settings.snowflake_warehouse, database=settings.snowflake_database)
    try:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT JOURNEY_DATE FROM RAIL_DELAY_ANALYTICS.ANALYTICS.FACT_STATION_ARRIVAL WHERE ARRIVAL_DELAY_MINUTES IS NOT NULL GROUP BY 1 ORDER BY 1")
            dates = [row[0] for row in cursor.fetchall()]
            test_start = dates[max(1, int(len(dates) * 0.8))]
            cursor.execute("""
                WITH training AS (SELECT TRAIN_NUMBER, STATION_CODE, ARRIVAL_DELAY_MINUTES FROM RAIL_DELAY_ANALYTICS.ANALYTICS.FACT_STATION_ARRIVAL WHERE JOURNEY_DATE < %s AND ARRIVAL_DELAY_MINUTES IS NOT NULL),
                means AS (SELECT TRAIN_NUMBER, STATION_CODE, AVG(ARRIVAL_DELAY_MINUTES) AS PREDICTION FROM training GROUP BY 1,2),
                global_mean AS (SELECT AVG(ARRIVAL_DELAY_MINUTES) AS VALUE FROM training),
                holdout AS (SELECT TRAIN_NUMBER, STATION_CODE, ARRIVAL_DELAY_MINUTES FROM RAIL_DELAY_ANALYTICS.ANALYTICS.FACT_STATION_ARRIVAL WHERE JOURNEY_DATE >= %s AND ARRIVAL_DELAY_MINUTES IS NOT NULL)
                SELECT COUNT(*), AVG(ABS(h.ARRIVAL_DELAY_MINUTES-COALESCE(m.PREDICTION,g.VALUE))), SQRT(AVG(POWER(h.ARRIVAL_DELAY_MINUTES-COALESCE(m.PREDICTION,g.VALUE),2))), AVG(ABS(h.ARRIVAL_DELAY_MINUTES-g.VALUE)) FROM holdout h CROSS JOIN global_mean g LEFT JOIN means m ON h.TRAIN_NUMBER=m.TRAIN_NUMBER AND h.STATION_CODE=m.STATION_CODE
            """, (test_start, test_start))
            rows, mae, rmse, global_mae = cursor.fetchone()
            accepted = float(mae) < float(global_mae)
            cursor.execute("INSERT INTO RAIL_DELAY_ANALYTICS.ML.MODEL_EVALUATION_AUDIT (EVALUATION_ID, MODEL_NAME, MODEL_VERSION, VALIDATION_ROW_COUNT, MAE, RMSE, BASELINE_MAE, ACCEPTED_FOR_PREDICTION) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (str(uuid.uuid4()), "train_station_historical_mean", "rstgcn_sep2024_chronological_v1", rows, mae, rmse, global_mae, accepted))
            connection.commit()
        finally:
            cursor.close()
    finally:
        connection.close()
    print(f"Chronological baseline succeeded; holdout starts {test_start}; rows={rows}; MAE={float(mae):.4f}; RMSE={float(rmse):.4f}; global-mean MAE={float(global_mae):.4f}; accepted={accepted}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Chronological baseline failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
