---
title: Example Workflow Dashboard
description: Example workflow data metrics and trends
---

# Example Workflow Dashboard

This dashboard presents key metrics from the example workflow data.

```sql summary_data
select
  date,
  record_count,
  type1_count,
  type2_count,
  average_value
from ${target_schema}.summary_table
order by date desc
```

## Summary Metrics

<Card>
  <Metric
    title="Total Records"
    value={sum(summary_data.record_count)}
    help="Total number of records processed"
  />
  <Metric
    title="Type 1 Records"
    value={sum(summary_data.type1_count)}
    help="Total number of Type 1 records"
  />
  <Metric
    title="Type 2 Records"
    value={sum(summary_data.type2_count)}
    help="Total number of Type 2 records"
  />
  <Metric
    title="Avg Value"
    value={average(summary_data.average_value)}
    valueFormat="0.0"
    help="Average value across all records"
  />
</Card>

## Trends Over Time

<LineChart
  data={summary_data}
  x="date"
  y="record_count"
  title="Total Records Processed Daily"
  yAxisTitle="Count"
/>

<LineChart
data={summary_data}
x="date"
y={["type1_count", "type2_count"]}
title="Records by Type"
yAxisTitle="Count"
/>

<LineChart
  data={summary_data}
  x="date"
  y="average_value"
  title="Average Value Trend"
  yAxisTitle="Value"
/>

## Recent Data

<DataTable
data={summary_data}
title="Recent Daily Summaries"
columns={[
"date",
"record_count",
"type1_count",
"type2_count",
"average_value"
]}
defaultPageSize={5}
/>
