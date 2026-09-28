with ranked as (
    select
        train_number::varchar as train_number,
        journey_date::date as journey_date,
        station_code::varchar as station_code,
        station_sequence::number as station_sequence,
        scheduled_arrival_at::timestamp_ntz as scheduled_arrival_at,
        actual_arrival_at::timestamp_ntz as actual_arrival_at,
        scheduled_departure_at::timestamp_ntz as scheduled_departure_at,
        actual_departure_at::timestamp_ntz as actual_departure_at,
        arrival_delay_minutes::number(12, 2) as arrival_delay_minutes,
        departure_delay_minutes::number(12, 2) as departure_delay_minutes,
        status::varchar as journey_status,
        source_record_hash,
        ingested_at,
        row_number() over (
            partition by train_number, journey_date, station_code, station_sequence
            order by ingested_at desc, source_record_hash desc
        ) as row_number
    from {{ source('raw', 'train_running_events') }}
)

select * exclude (row_number)
from ranked
where row_number = 1
