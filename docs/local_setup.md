# Local setup and boundaries

The repository owns source code, SQL, dbt project files, tests, CI, and safe templates.
Your local user profile owns authentication and secrets, so it is intentionally outside Git.

## What is automated in the repository

- Project-local Python environment and pinned dependency specification
- Python CLI and unit tests
- dbt model dependencies and parse/build commands
- Snowflake setup and object DDL
- GitHub Actions definitions (daily workflow is opt-in)

## What must remain user-controlled

- Snowflake account creation, authentication, and billing settings
- Values in `.env` and `~/.dbt/profiles.yml`
- GitHub authentication and repository publication

When the terminal runner is healthy, the intended local bootstrap is a single command
sequence documented in the README. The tracked profile template is
`dbt_railway/profiles.yml.example`; it contains no credential.
