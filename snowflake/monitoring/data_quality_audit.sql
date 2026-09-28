create table if not exists RAIL_DELAY_ANALYTICS.AUDIT.DATA_QUALITY_AUDIT (
    quality_check_id varchar not null,
    run_id varchar not null,
    test_name varchar not null,
    severity varchar not null,
    failed_row_count number not null,
    checked_at timestamp_ntz not null default current_timestamp(),
    status varchar not null,
    primary key (quality_check_id)
);
