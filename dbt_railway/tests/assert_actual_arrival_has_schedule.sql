select *
from {{ ref('stg_train_running') }}
where actual_arrival_at is not null
  and scheduled_arrival_at is null
