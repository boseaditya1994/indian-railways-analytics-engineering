create table if not exists RAIL_DELAY_ANALYTICS.AUDIT.RECONCILIATION_AUDIT (
    reconciliation_id varchar not null,
    run_id varchar not null,
    dataset varchar not null,
    source_count number not null,
    raw_count number not null,
    staging_count number not null,
    mart_count number not null,
    rejected_count number not null,
    duplicate_count number not null,
    reconciled_at timestamp_ntz not null default current_timestamp(),
    status varchar not null,
    primary key (reconciliation_id)
);
