{{ config(
    unique_key=['train_number', 'journey_date', 'station_code', 'station_sequence'],
    incremental_strategy='merge',
    on_schema_change='sync_all_columns'
) }}

select
    train_number,
    journey_date,
    station_code,
    station_sequence,
    scheduled_arrival_at,
    actual_arrival_at,
    scheduled_departure_at,
    actual_departure_at,
    coalesce(arrival_delay_minutes, derived_arrival_delay_minutes) as arrival_delay_minutes,
    departure_delay_minutes,
    previous_station_arrival_delay_minutes,
    journey_status,
    source_record_hash,
    ingested_at
from {{ ref('int_train_running_enriched') }}
{% if is_incremental() %}
where ingested_at >= (
    select dateadd('hour', -48, coalesce(max(ingested_at), '1900-01-01'::timestamp_ntz))
    from {{ this }}
)
{% endif %}
