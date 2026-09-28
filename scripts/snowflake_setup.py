"""Apply reviewed project DDL using the existing account-managed warehouse.

This script creates only the project database, schemas, and tables defined in versioned
SQL files. It never creates, resizes, resumes, suspends, or alters a warehouse.
"""

from __future__ import annotations

from getpass import getpass
from pathlib import Path

from railway_pipeline.config.settings import Settings


SQL_FILES = (
    "snowflake/setup/001_database_and_schemas.sql",
    "snowflake/objects/ingestion_audit.sql",
    "snowflake/objects/raw_train_running_events.sql",
    "snowflake/objects/raw_train_schedule.sql",
    "snowflake/objects/predictions.sql",
    "snowflake/monitoring/reconciliation_audit.sql",
    "snowflake/monitoring/data_quality_audit.sql",
)


def statements(sql: str) -> list[str]:
    """Split this repository's simple DDL files into executable statements."""
    without_comments = "\n".join(line for line in sql.splitlines() if not line.lstrip().startswith("--"))
    return [statement.strip() for statement in without_comments.split(";") if statement.strip()]


def main() -> None:
    settings = Settings()
    password = getpass("Snowflake password (entered locally; not stored): ")
    import snowflake.connector

    root = Path(__file__).resolve().parent.parent
    connection = snowflake.connector.connect(
        account=settings.snowflake_account,
        user=settings.snowflake_user,
        password=password,
        role=settings.snowflake_role,
        warehouse=settings.snowflake_warehouse,
    )
    try:
        with connection.cursor() as cursor:
            for relative_path in SQL_FILES:
                sql_path = root / relative_path
                for statement in statements(sql_path.read_text(encoding="utf-8")):
                    cursor.execute(statement)
                print(f"Applied: {relative_path}")
    finally:
        connection.close()
    print("Snowflake project objects are ready.")


if __name__ == "__main__":
    main()
