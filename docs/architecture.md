# Architecture decisions

The system is batch-first. Python ingests approved sources into Snowflake RAW; dbt
builds staging, intermediate, dimensional, analytics, and feature models. A Python
training process consumes only time-safe features. React consumes a server-side API or
published mart extract, never Snowflake credentials.

Daily ingestion is a scheduled batch process, not real-time streaming. Its scope and
cadence must follow the authorized source's limits and terms. The project uses the
account-managed `COMPUTE_WH` by default and does not create or alter a warehouse.
