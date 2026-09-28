select
    train_number,
    count(*) as station_stop_observations,
    avg(arrival_delay_minutes) as average_arrival_delay_minutes,
    median(arrival_delay_minutes) as median_arrival_delay_minutes,
    avg(iff(arrival_delay_minutes <= 0, 1, 0)) * 100 as on_time_or_early_percent,
    avg(iff(arrival_delay_minutes > 60, 1, 0)) * 100 as major_delay_percent
from {{ ref('fact_station_arrival') }}
where arrival_delay_minutes is not null
group by 1
