select distinct
    train_number,
    train_name,
    train_type,
    source_station_code as origin_station_code,
    destination_station_code,
    source_name,
    ingested_at as record_updated_at
from {{ ref('stg_train_schedule') }}
