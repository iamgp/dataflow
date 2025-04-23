{{
    config(
        materialized='table',
        schema='nightscout',
        description='Processed Nightscout treatment events'
    )
}}

-- Transform raw Nightscout treatments data into a clean, analysis-ready table
with raw_treatments as (
    select
        value as treatment_data,
        metadata
    from {{ source('raw_data', 'nightscout_treatments') }}
),

extracted_treatments as (
    select
        json_extract(treatment_data, '$.eventType') as event_type,
        cast(json_extract(treatment_data, '$.created_at') as timestamp) as event_time,
        case
            when json_extract(treatment_data, '$.insulin') != 'null'
            then cast(json_extract(treatment_data, '$.insulin') as float)
            else null
        end as insulin_amount,
        case
            when json_extract(treatment_data, '$.carbs') != 'null'
            then cast(json_extract(treatment_data, '$.carbs') as float)
            else null
        end as carb_amount,
        json_extract(treatment_data, '$.notes') as notes,
        json_extract(treatment_data, '$.enteredBy') as entered_by,
        cast(json_extract(metadata, '$.ingestion_timestamp') as timestamp) as ingestion_time
    from raw_treatments
)

select
    event_type,
    event_time,
    insulin_amount,
    carb_amount,
    notes,
    entered_by,
    ingestion_time,
    -- Derived fields for analysis
    date_trunc('day', event_time) as event_date,
    date_trunc('hour', event_time) as event_hour,
    case
        when event_type = 'Meal Bolus' then 'Meal'
        when event_type = 'Correction Bolus' then 'Correction'
        when event_type = 'Basal' then 'Basal'
        when event_type = 'Carb Correction' then 'Carbs'
        else event_type
    end as event_category
from extracted_treatments
order by event_time desc
