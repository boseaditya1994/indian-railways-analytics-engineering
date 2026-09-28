create table if not exists RAIL_DELAY_ANALYTICS.AUDIT.INGESTION_RUN_AUDIT (
    run_id varchar not null,
    pipeline_name varchar not null,
    dataset varchar not null,
    source_name varchar not null,
    watermark_at timestamp_ntz,
    started_at timestamp_ntz not null,
    completed_at timestamp_ntz,
    records_received number default 0,
    records_inserted number default 0,
    records_updated number default 0,
    records_rejected number default 0,
    status varchar not null,
    error_message varchar,
    primary key (run_id)
);
