---
title: Workflow Dashboard
description: Main dashboard for workflow metrics and KPIs
---

# Workflow Dashboard

This dashboard provides an overview of key metrics and KPIs from the workflow.

```sql summary_query
select
  date,
  record_count,
  type1_count,
  type2_count,
  average_value
from ${target_schema}.summary_table
order by date desc
```

## Key Metrics

<Card>
  <Metric
    title="Total Records"
    value={sum(summary_query.record_count)}
    help="Total number of records processed by the workflow"
  />
  <Metric
    title="Average Value"
    value={average(summary_query.average_value)}
    valueFormat="0.00"
    help="Average value across all records"
  />
  <Metric
    title="Type 1 Records"
    value={sum(summary_query.type1_count)}
    help="Total number of Type 1 records"
  />
  <Metric
    title="Type 2 Records"
    value={sum(summary_query.type2_count)}
    help="Total number of Type 2 records"
  />
</Card>

## Trend Analysis

<LineChart
data={summary_query}
x="date"
y={["record_count", "type1_count", "type2_count"]}
title="Records Processed Over Time"
yAxisTitle="Count"
xAxisTitle="Date"
/>

## Daily Average Values

<LineChart
  data={summary_query}
  x="date"
  y="average_value"
  title="Average Value Over Time"
  yAxisTitle="Average Value"
  xAxisTitle="Date"
/>

## Breakdown by Type

```sql type_breakdown
select
  date,
  type1_count,
  type2_count,
  type1_count + type2_count as total_count,
  type1_count / nullif(type1_count + type2_count, 0) * 100 as type1_percent,
  type2_count / nullif(type1_count + type2_count, 0) * 100 as type2_percent
from ${target_schema}.summary_table
order by date desc
```

<BarChart
data={type_breakdown}
x="date"
y={["type1_percent", "type2_percent"]}
title="Daily Distribution by Type"
yAxisTitle="Percentage (%)"
xAxisTitle="Date"
type="stacked-100%"
/>

## Recent Data

<DataTable
  data={summary_query}
  title="Recent Daily Summaries"
/>

For more detailed analysis, check out the [Detailed Metrics](/details) page.
