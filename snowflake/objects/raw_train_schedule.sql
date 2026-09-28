create table if not exists RAIL_DELAY_ANALYTICS.RAW.TRAIN_SCHEDULE_STOPS (
    train_number varchar not null,
    train_name varchar,
    train_type varchar,
    source_station_code varchar,
    destination_station_code varchar,
    station_code varchar not null,
    station_name varchar,
    station_sequence number not null,
    schedule_arrival_time varchar,
    schedule_departure_time varchar,
    journey_day_number number,
    distance_km number(12, 2),
    source_name varchar not null,
    source_record_hash varchar not null,
    ingested_at timestamp_ntz not null default current_timestamp(),
    run_id varchar not null
);
