{{
    config(
        materialized='table',
        schema='nightscout',
        description='Daily summary of glucose readings and treatments'
    )
}}

with daily_readings as (
    select
        reading_date,
        count(*) as reading_count,
        round(avg(glucose_value), 1) as avg_glucose,
        min(glucose_value) as min_glucose,
        max(glucose_value) as max_glucose,
        count(case when range_category = 'Low' then 1 end) as low_count,
        count(case when range_category = 'In Range' then 1 end) as in_range_count,
        count(case when range_category = 'High' then 1 end) as high_count,
        round(count(case when range_category = 'In Range' then 1 end) * 100.0 / count(*), 1) as time_in_range_pct
    from {{ ref('readings') }}
    group by reading_date
),

daily_treatments as (
    select
        event_date,
        sum(case when insulin_amount is not null then insulin_amount else 0 end) as total_insulin,
        sum(case when carb_amount is not null then carb_amount else 0 end) as total_carbs,
        count(case when event_type like '%Bolus%' then 1 end) as bolus_count,
        count(case when event_type = 'Meal Bolus' then 1 end) as meal_bolus_count,
        count(case when event_type = 'Correction Bolus' then 1 end) as correction_bolus_count
    from {{ ref('treatments') }}
    group by event_date
)

select
    r.reading_date as date,
    r.reading_count,
    r.avg_glucose,
    r.min_glucose,
    r.max_glucose,
    r.low_count,
    r.in_range_count,
    r.high_count,
    r.time_in_range_pct,
    coalesce(t.total_insulin, 0) as total_insulin,
    coalesce(t.total_carbs, 0) as total_carbs,
    coalesce(t.bolus_count, 0) as bolus_count,
    coalesce(t.meal_bolus_count, 0) as meal_bolus_count,
    coalesce(t.correction_bolus_count, 0) as correction_bolus_count,
    -- Calculate insulin-to-carb ratio if both values exist
    case
        when coalesce(t.total_carbs, 0) > 0 and coalesce(t.total_insulin, 0) > 0
        then round(t.total_carbs / t.total_insulin, 1)
        else null
    end as carb_insulin_ratio
from daily_readings r
left join daily_treatments t on r.reading_date = t.event_date
order by r.reading_date desc
