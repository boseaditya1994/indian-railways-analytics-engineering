with ranked as (
    select
        train_number::varchar as train_number,
        train_name::varchar as train_name,
        train_type::varchar as train_type,
        source_station_code::varchar as source_station_code,
        destination_station_code::varchar as destination_station_code,
        station_code::varchar as station_code,
        station_name::varchar as station_name,
        station_sequence::number as station_sequence,
        schedule_arrival_time::varchar as schedule_arrival_time,
        schedule_departure_time::varchar as schedule_departure_time,
        journey_day_number::number as journey_day_number,
        distance_km::number(12, 2) as distance_km,
        source_name,
        source_record_hash,
        ingested_at,
        row_number() over (
            partition by train_number, station_code, station_sequence
            order by ingested_at desc, source_record_hash desc
        ) as row_number
    from {{ source('raw', 'train_schedule_stops') }}
)

select * exclude (row_number)
from ranked
where row_number = 1
