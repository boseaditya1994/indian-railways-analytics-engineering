{{ config(
    unique_key=['train_number', 'journey_date', 'station_code', 'station_sequence'],
    incremental_strategy='merge'
) }}

with base as (
    select * from {{ ref('fact_station_arrival') }}
), features as (
    select
        train_number,
        journey_date,
        station_code,
        station_sequence,
        scheduled_arrival_at as prediction_at,
        previous_station_arrival_delay_minutes,
        dayofweek(scheduled_arrival_at) as scheduled_arrival_day_of_week,
        hour(scheduled_arrival_at) as scheduled_arrival_hour,
        arrival_delay_minutes as target_arrival_delay_minutes
    from base
)
select * from features
