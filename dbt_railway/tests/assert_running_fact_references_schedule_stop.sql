select f.*
from {{ ref('fact_station_arrival') }} f
left join {{ ref('dim_route_stop') }} s
    on f.train_number = s.train_number
    and f.station_code = s.station_code
    and f.station_sequence = s.station_sequence
where s.train_number is null
