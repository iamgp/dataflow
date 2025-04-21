# Example Workflow Dashboard

This is a sample dashboard for the Example Workflow. In a real workflow, this would display data processed by the workflow.

## Workflow Performance

```sql example_metrics
-- This is a mock query for demonstration purposes
-- In a real workflow, this would query actual data from your database
SELECT
  '2023-01-01' as date,
  100 as records_processed,
  95 as successful_records,
  5 as failed_records,
  95.0 as success_rate
UNION ALL
SELECT
  '2023-01-02' as date,
  150 as records_processed,
  147 as successful_records,
  3 as failed_records,
  98.0 as success_rate
UNION ALL
SELECT
  '2023-01-03' as date,
  200 as records_processed,
  196 as successful_records,
  4 as failed_records,
  98.0 as success_rate
UNION ALL
SELECT
  '2023-01-04' as date,
  180 as records_processed,
  176 as successful_records,
  4 as failed_records,
  97.8 as success_rate
UNION ALL
SELECT
  '2023-01-05' as date,
  210 as records_processed,
  210 as successful_records,
  0 as failed_records,
  100.0 as success_rate
```

<LineChart
  data={example_metrics}
  x="date"
  y="records_processed"
  title="Daily Records Processed"
/>

<LineChart
data={example_metrics}
x="date"
y={["successful_records", "failed_records"]}
title="Success vs Failure"
/>

<BigValue
  data={example_metrics}
  value="records_processed"
  title="Total Records (Last 5 Days)"
  aggregation="sum"
/>

<BigValue
  data={example_metrics}
  value="success_rate"
  title="Average Success Rate"
  aggregation="mean"
  maxDecimals={1}
  suffix="%"
/>

## Detailed Metrics

<DataTable
  data={example_metrics}
  link="details/{date}"
/>

When connecting to real data, you would:

1. Replace the mock queries with real queries against your database
2. Use the data processing tables created by your workflow
3. Create additional pages with more detailed analysis

## Next Steps

- [Documentation](/docs)
- [Workflow Analysis](/analysis)
