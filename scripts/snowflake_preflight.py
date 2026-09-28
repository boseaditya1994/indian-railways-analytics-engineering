"""Browser-authenticated, read-only Snowflake preflight.

The script intentionally creates no database, warehouse, schema, role, or table.
"""

from __future__ import annotations

from getpass import getpass

from railway_pipeline.config.settings import Settings


def main() -> None:
    settings = Settings()
    if not settings.snowflake_account or not settings.snowflake_user:
        raise SystemExit("SNOWFLAKE_ACCOUNT and SNOWFLAKE_USER are required in .env")

    import snowflake.connector

    password = getpass("Snowflake password (entered locally; not stored): ")
    connection = snowflake.connector.connect(
        account=settings.snowflake_account,
        user=settings.snowflake_user,
        password=password,
        warehouse=settings.snowflake_warehouse,
        role=settings.snowflake_role,
    )
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "select current_account(), current_user(), current_role(), current_warehouse(), current_database()"
            )
            account, user, role, warehouse, database = cursor.fetchone()
            print("Snowflake preflight succeeded")
            print(f"Account: {account}")
            print(f"User: {user}")
            print(f"Role: {role}")
            print(f"Warehouse: {warehouse}")
            print(f"Database: {database}")
            cursor.execute("show warehouses like 'COMPUTE_WH'")
            warehouse_rows = cursor.fetchall()
            print(f"COMPUTE_WH found: {bool(warehouse_rows)}")
        finally:
            cursor.close()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
