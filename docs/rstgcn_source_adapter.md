# RSTGCN source adapter

The RSTGCN repository documents two relevant September-2024 files:

- `train_routes_delays_Sep2024.csv`: one train + date + station delay observation.
- `train_routes_Sep2024.csv`: train route and station sequence.

`rstgcn_adapter.py` joins them to produce the required canonical key: train number,
journey date, station code, station sequence. Any delay record with no matching schedule
stop is intentionally emitted with sequence `0` so the validation layer quarantines it.

Use this adapter only after written reuse permission or a formal compatible licence is
recorded. Raw RSTGCN files must remain outside Git.
