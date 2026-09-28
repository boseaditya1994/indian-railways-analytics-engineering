select *
from {{ ref('stg_train_running') }}
where station_sequence <= 0
