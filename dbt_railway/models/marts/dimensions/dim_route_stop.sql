select
    train_number,
    station_code,
    station_sequence,
    journey_day_number,
    distance_km,
    schedule_arrival_time,
    schedule_departure_time,
    source_name,
    ingested_at as record_updated_at
from {{ ref('stg_train_schedule') }}
