"""Store the Snowflake archive password in the current user's Windows Credential Manager."""

from __future__ import annotations

import os
import sys

from archive_raildar_live_status import CREDENTIAL_SERVICE, _credential_username, _load_local_env

from railway_pipeline.config.settings import Settings


def main() -> None:
    _load_local_env()
    password = os.environ.pop("RAILWAY_ARCHIVE_SNOWFLAKE_PASSWORD", None)
    if not password:
        raise RuntimeError("Password input was not supplied by the secure setup script.")
    try:
        import keyring
    except ImportError as exc:
        raise RuntimeError("Install the scheduler dependency: pip install -e '.[scheduler]'.") from exc
    keyring.set_password(CREDENTIAL_SERVICE, _credential_username(Settings()), password)
    print("Snowflake archive credential stored in Windows Credential Manager for the current Windows user.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Could not store Snowflake archive credential: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
