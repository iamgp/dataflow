---
title: Hourly Glucose Patterns
description: Time-based analysis of glucose patterns
---

# Hourly Glucose Patterns

This dashboard helps identify time-based patterns in glucose readings.

```sql hourly_patterns
with hourly_data as (
  select
    date_trunc('hour', reading_time) as hour,
    extract(hour from reading_time) as hour_of_day,
    avg(glucose_value) as avg_glucose,
    count(*) as reading_count,
    count(case when range_category = 'Low' then 1 end) as low_count,
    count(case when range_category = 'In Range' then 1 end) as in_range_count,
    count(case when range_category = 'High' then 1 end) as high_count
  from ${target_schema}.readings
  group by hour, hour_of_day
)

select
  hour_of_day,
  avg(avg_glucose) as avg_glucose,
  avg(low_count * 100.0 / reading_count) as low_percentage,
  avg(in_range_count * 100.0 / reading_count) as in_range_percentage,
  avg(high_count * 100.0 / reading_count) as high_percentage,
  count(distinct date_trunc('day', hour)) as day_count
from hourly_data
group by hour_of_day
order by hour_of_day
```

```sql day_of_week_patterns
with day_data as (
  select
    reading_date,
    extract(dow from reading_date) as day_of_week,
    avg_glucose,
    time_in_range_pct
  from ${target_schema}.daily_summary
)

select
  day_of_week,
  case day_of_week
    when 0 then 'Sunday'
    when 1 then 'Monday'
    when 2 then 'Tuesday'
    when 3 then 'Wednesday'
    when 4 then 'Thursday'
    when 5 then 'Friday'
    when 6 then 'Saturday'
  end as day_name,
  avg(avg_glucose) as avg_glucose,
  avg(time_in_range_pct) as avg_time_in_range,
  count(*) as day_count
from day_data
group by day_of_week, day_name
order by day_of_week
```

## Hourly Analysis

<LineChart
  data={hourly_patterns}
  x="hour_of_day"
  y="avg_glucose"
  title="Average Glucose by Hour of Day"
  xAxisTitle="Hour of Day"
  yAxisTitle="Glucose (mg/dL)"
  yMin={70}
  yMax={200}
/>

<BarChart
data={hourly_patterns}
x="hour_of_day"
y={["low_percentage", "in_range_percentage", "high_percentage"]}
title="Glucose Ranges by Hour of Day"
colors={["#FF4560", "#00E396", "#FEB019"]}
type="stacked"
xAxisTitle="Hour of Day"
yAxisTitle="Percentage"
/>

## Daily Patterns

<BarChart
  data={day_of_week_patterns}
  x="day_name"
  y="avg_glucose"
  title="Average Glucose by Day of Week"
  xAxisTitle="Day of Week"
  yAxisTitle="Glucose (mg/dL)"
  yMin={70}
  yMax={200}
/>

<BarChart
data={day_of_week_patterns}
x="day_name"
y="avg_time_in_range"
title="Time In Range by Day of Week"
xAxisTitle="Day of Week"
yAxisTitle="Percentage"
colors={["#00E396"]}
yMin={0}
yMax={100}
/>

## Raw Data

<DataTable
  data={hourly_patterns}
  title="Hourly Pattern Data"
/>

<DataTable
  data={day_of_week_patterns}
  title="Day of Week Pattern Data"
/>
