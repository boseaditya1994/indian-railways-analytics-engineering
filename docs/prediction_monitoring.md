# Prediction monitoring

Predictions are immutable model outputs at a specific time and target station. Later
actuals are populated separately so error calculation is auditable.

Promotion requires a chronological validation result that improves on the mandatory
baseline MAE. Production monitoring tracks evaluated prediction count, MAE, RMSE, feature
freshness, null rates, and model version. Any confidence interval requires a separate
calibration and coverage analysis; no placeholder confidence is shown.
