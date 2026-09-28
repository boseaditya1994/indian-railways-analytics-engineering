create table if not exists RAIL_DELAY_ANALYTICS.RAW.TRAIN_RUNNING_EVENTS (
    train_number varchar not null,
    journey_date date not null,
    station_code varchar not null,
    station_sequence number not null,
    scheduled_arrival_at timestamp_ntz,
    actual_arrival_at timestamp_ntz,
    scheduled_departure_at timestamp_ntz,
    actual_departure_at timestamp_ntz,
    arrival_delay_minutes number(12, 2),
    departure_delay_minutes number(12, 2),
    status varchar,
    source_name varchar not null,
    source_record_hash varchar not null,
    source_observed_at timestamp_ntz,
    ingested_at timestamp_ntz not null default current_timestamp(),
    run_id varchar not null
);

-- The hash is part of the idempotency contract. Duplicate natural keys are resolved in dbt
-- by most-recent ingestion time; source records remain immutable in RAW for auditability.
