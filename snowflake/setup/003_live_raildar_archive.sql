CREATE SCHEMA IF NOT EXISTS RAIL_DELAY_ANALYTICS.LIVE;

CREATE TABLE IF NOT EXISTS RAIL_DELAY_ANALYTICS.LIVE.RAILRADAR_TRAIN_STATUS_SNAPSHOTS (
    snapshot_id VARCHAR NOT NULL,
    run_id VARCHAR NOT NULL,
    source_name VARCHAR NOT NULL,
    train_number VARCHAR NOT NULL,
    journey_date DATE,
    provider_updated_at TIMESTAMP_TZ,
    retrieved_at TIMESTAMP_TZ NOT NULL,
    journey_status VARCHAR,
    delay_minutes NUMBER(12, 2),
    current_station_code VARCHAR,
    next_station_code VARCHAR,
    next_station_name VARCHAR,
    source_record_hash VARCHAR NOT NULL,
    created_at TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (snapshot_id)
);
