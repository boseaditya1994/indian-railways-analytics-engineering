# Incremental ingestion strategy

Each source extract is assigned a `run_id` and recorded in `AUDIT.INGESTION_RUN_AUDIT`.
The latest successful source-observation watermark is read before the next run. Daily
loads re-read a 48-hour overlap window because current journey records can be corrected
after initial publication.

Raw records are immutable. A SHA-256 hash of canonical source content supports exact
source-payload deduplication; the dbt staging model then resolves repeated natural keys
by the most recently ingested record. Invalid records are quarantined with their source
hash and validation reason. Missing actual timestamps/delays remain null, never zero.
