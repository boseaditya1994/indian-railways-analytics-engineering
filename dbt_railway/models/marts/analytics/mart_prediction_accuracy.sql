select
    model_name,
    model_version,
    count_if(actual_arrival_delay_minutes is not null) as evaluated_prediction_count,
    avg(absolute_error_minutes) as mae_minutes,
    sqrt(avg(power(actual_arrival_delay_minutes - predicted_arrival_delay_minutes, 2))) as rmse_minutes
from {{ source('ml', 'fact_prediction') }}
group by 1, 2
