# Dimensional model implementation

Schedule data is modeled independently of actual running data so the platform can retain
an honest distinction between planned service and observed performance.

| Model | Grain | Purpose |
| --- | --- | --- |
| `dim_train` | train number | current train master attributes |
| `dim_station` | station code | current station master attributes |
| `dim_route_stop` | train + station + sequence | planned timetable stop |
| `fact_station_arrival` | train + journey date + station stop | observed running performance |
| `mart_train_punctuality` | train | train-level performance aggregate |
| `mart_station_delay` | station | station-level performance aggregate |

The analytical categories in future dashboard work will be explicitly labeled as project
thresholds rather than official Indian Railways definitions.
