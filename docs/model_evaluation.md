# Model evaluation and monitoring

The train-route historical mean baseline is mandatory. A candidate ML model is accepted
only when it improves held-out chronological MAE and does not materially degrade RMSE.

## Split strategy

- Train on earlier journey dates.
- Validate on the next chronological period.
- Test once on the final untouched period.
- Never randomly split station-stop records across time.

## Operational monitoring

For every model version, record prediction volume, feature null rates, feature freshness,
later actual values, MAE, RMSE, and baseline comparison. Do not display confidence until
coverage has been empirically calibrated.
