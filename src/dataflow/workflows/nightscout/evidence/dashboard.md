---
title: Nightscout Dashboard
description: Glucose monitoring and insulin/carb tracking
---

# Nightscout Analytics Dashboard

This dashboard provides insights into glucose trends, time in range, and insulin/carb data.

```sql daily_summary
select *
from ${target_schema}.daily_summary
order by date desc
limit 14
```

```sql recent_readings
select
  reading_time,
  glucose_value,
  trend,
  range_category
from ${target_schema}.readings
order by reading_time desc
limit 100
```

```sql recent_treatments
select
  event_time,
  event_type,
  insulin_amount,
  carb_amount,
  notes
from ${target_schema}.treatments
order by event_time desc
limit 20
```

## Summary Metrics (Last 14 Days)

<Card>
  <Metric
    title="Average Glucose"
    value={average(daily_summary.avg_glucose)}
    valueFormat="0"
    suffix=" mg/dL"
    help="Average glucose over the period"
  />
  <Metric
    title="Time In Range"
    value={average(daily_summary.time_in_range_pct)}
    valueFormat="0.0"
    suffix="%"
    help="Percentage of readings in target range (70-180 mg/dL)"
  />
  <Metric
    title="Daily Insulin"
    value={average(daily_summary.total_insulin)}
    valueFormat="0.0"
    suffix=" units"
    help="Average daily insulin"
  />
  <Metric
    title="Daily Carbs"
    value={average(daily_summary.total_carbs)}
    valueFormat="0"
    suffix=" g"
    help="Average daily carbohydrates"
  />
</Card>

## Glucose Trends

<LineChart
  data={daily_summary}
  x="date"
  y="avg_glucose"
  title="Average Daily Glucose"
  yAxisTitle="mg/dL"
  yMin={60}
  yMax={250}
/>

<BarChart
data={daily_summary}
x="date"
y={["low_count", "in_range_count", "high_count"]}
title="Daily Readings by Range"
colors={["#FF4560", "#00E396", "#FEB019"]}
type="stacked"
yAxisTitle="Count"
/>

<AreaChart
data={daily_summary}
x="date"
y="time_in_range_pct"
title="Time In Range"
yAxisTitle="Percentage"
colors={["#00E396"]}
yMin={0}
yMax={100}
/>

## Insulin & Carbs

<BarChart
data={daily_summary}
x="date"
y={["total_insulin"]}
title="Daily Insulin"
yAxisTitle="Units"
colors={["#008FFB"]}
/>

<BarChart
data={daily_summary}
x="date"
y={["total_carbs"]}
title="Daily Carbs"
yAxisTitle="Grams"
colors={["#FEB019"]}
/>

<LineChart
  data={daily_summary}
  x="date"
  y="carb_insulin_ratio"
  title="Carb to Insulin Ratio"
  yAxisTitle="Ratio"
  connectNulls={true}
/>

## Recent Data

### Recent Glucose Readings

<DataTable
  data={recent_readings}
  title="Recent Glucose Readings"
  rowsPerPage={5}
/>

### Recent Treatments

<DataTable
  data={recent_treatments}
  title="Recent Treatments"
  rowsPerPage={5}
/>
