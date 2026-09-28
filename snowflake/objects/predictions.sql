create table if not exists RAIL_DELAY_ANALYTICS.ML.FACT_PREDICTION (
    prediction_id varchar not null,
    model_name varchar not null,
    model_version varchar not null,
    prediction_at timestamp_ntz not null,
    train_number varchar not null,
    journey_date date not null,
    target_station_code varchar not null,
    target_station_sequence number not null,
    predicted_arrival_delay_minutes number(12, 2) not null,
    actual_arrival_delay_minutes number(12, 2),
    absolute_error_minutes number(12, 2),
    feature_freshness_at timestamp_ntz,
    created_at timestamp_ntz not null default current_timestamp(),
    primary key (prediction_id)
);

create table if not exists RAIL_DELAY_ANALYTICS.ML.MODEL_EVALUATION_AUDIT (
    evaluation_id varchar not null,
    model_name varchar not null,
    model_version varchar not null,
    evaluated_at timestamp_ntz not null default current_timestamp(),
    validation_row_count number not null,
    mae number(12, 4) not null,
    rmse number(12, 4) not null,
    baseline_mae number(12, 4) not null,
    accepted_for_prediction boolean not null,
    primary key (evaluation_id)
);
