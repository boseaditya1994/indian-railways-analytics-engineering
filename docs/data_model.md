# Data model

## `fact_station_arrival`

- **Grain:** train number + journey date + station code + station sequence
- **Unique key:** the four grain fields above
- **Measures:** arrival/departure delay minutes, scheduled/actual timestamps
- **Dimensions:** train, date, station, route stop, status

## `fct_delay_features`

- **Grain:** a future target stop for one train journey
- **Features:** schedule hour/day, prior-stop observed delay, and historical aggregates
  that end before the prediction timestamp
- **Target:** actual arrival delay minutes, retained only for training/evaluation

## `fact_prediction`

- **Grain:** model version + prediction timestamp + train journey + target station
- **Measures:** prediction, later actual, absolute error, model metadata
