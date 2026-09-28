-- Read-only Snowflake account preflight. Run before executing any project DDL.
select current_account() as account_locator,
       current_user() as user_name,
       current_role() as current_role,
       current_warehouse() as current_warehouse,
       current_database() as current_database;

show warehouses like 'COMPUTE_WH';
