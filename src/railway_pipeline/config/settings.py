"""Environment-backed settings; credentials are never hard-coded."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    railway_env: str = "local"
    log_level: str = "INFO"
    snowflake_account: str | None = None
    snowflake_user: str | None = None
    snowflake_password: str | None = None
    snowflake_role: str = "RAIL_DELAY_ENGINEER"
    snowflake_warehouse: str = "COMPUTE_WH"
    snowflake_database: str = "RAIL_DELAY_ANALYTICS"
    snowflake_schema: str = "RAW"
    railradar_api_key: str | None = None
