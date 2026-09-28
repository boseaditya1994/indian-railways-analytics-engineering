with ranked as (
    select
        station_code,
        station_name,
        source_name,
        ingested_at as record_updated_at,
        row_number() over (
            partition by station_code
            order by (station_name is not null) desc, ingested_at desc, station_name asc
        ) as row_number
    from {{ ref('stg_train_schedule') }}
)

select * exclude (row_number)
from ranked
where row_number = 1
