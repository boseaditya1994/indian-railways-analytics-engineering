# Data directory

No third-party source data is committed here by default. Place an approved source file in
`data/raw/` only after its license, coverage, provenance, and automated-access permission
are recorded in `data/provenance/`.

The historical CSV adapter expects the following minimum columns:

`train_number`, `journey_date`, `station_code`, `station_sequence`

Additional schedule/actual timestamp and delay fields are validated when present.
