select
    *,
    lag(arrival_delay_minutes) over (
        partition by train_number, journey_date order by station_sequence
    ) as previous_station_arrival_delay_minutes,
    case
        when actual_arrival_at is not null and scheduled_arrival_at is not null
            then datediff('minute', scheduled_arrival_at, actual_arrival_at)
    end as derived_arrival_delay_minutes
from {{ ref('stg_train_running') }}
