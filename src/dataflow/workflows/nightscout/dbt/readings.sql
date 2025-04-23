{{
    config(
        materialized='table',
        schema='nightscout',
        description='Processed Nightscout glucose readings'
    )
}}

-- Transform raw Nightscout entries data into a clean, analysis-ready table
with raw_entries as (
    select
        value as entry_data,
        metadata
    from {{ source('raw_data', 'nightscout_entries') }}
),

extracted_entries as (
    select
        cast(json_extract(entry_data, '$.date') as timestamp) as reading_time,
        cast(json_extract(entry_data, '$.sgv') as integer) as glucose_value,
        json_extract(entry_data, '$.device') as device,
        json_extract(entry_data, '$.direction') as trend,
        json_extract(entry_data, '$.type') as reading_type,
        cast(json_extract(entry_data, '$.noise') as integer) as noise,
        cast(json_extract(metadata, '$.ingestion_timestamp') as timestamp) as ingestion_time
    from raw_entries
    where json_extract(entry_data, '$.sgv') is not null
)

select
    reading_time,
    glucose_value,
    device,
    trend,
    reading_type,
    noise,
    ingestion_time,
    -- Derived fields for analysis
    case
        when glucose_value < 70 then 'Low'
        when glucose_value > 180 then 'High'
        else 'In Range'
    end as range_category,
    date_trunc('day', reading_time) as reading_date,
    date_trunc('hour', reading_time) as reading_hour
from extracted_entries
order by reading_time desc
