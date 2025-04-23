---
title: Nightscout Analytics
description: Comprehensive glucose monitoring analytics
---

# Nightscout Analytics

Welcome to the Nightscout analytics platform. This suite of dashboards provides comprehensive insights into glucose patterns, treatment effectiveness, and trends over time.

## Available Dashboards

<Card>
  <LinkButton url="/dashboard" iconRight="arrow-right">
    Main Dashboard
  </LinkButton>
  <p>Overview of glucose trends, time in range, and insulin/carb data</p>
</Card>

<Card>
  <LinkButton url="/hourly_patterns" iconRight="arrow-right">
    Hourly Patterns
  </LinkButton>
  <p>Time-based analysis to identify patterns by hour of day and day of week</p>
</Card>

## Key Metrics (Last 7 Days)

```sql recent_metrics
select
  avg(avg_glucose) as avg_glucose,
  avg(time_in_range_pct) as time_in_range,
  avg(total_insulin) as avg_insulin,
  avg(total_carbs) as avg_carbs
from ${target_schema}.daily_summary
order by date desc
limit 7
```

<BigValue
  data={recent_metrics}
  value='avg_glucose'
  title='Average Glucose'
  valueFormat='0'
  suffix=' mg/dL'
/>

<BigValue
  data={recent_metrics}
  value='time_in_range'
  title='Time in Range'
  valueFormat='0.0'
  suffix='%'
/>

<BigValue
  data={recent_metrics}
  value='avg_insulin'
  title='Avg Daily Insulin'
  valueFormat='0.0'
  suffix=' units'
/>

<BigValue
  data={recent_metrics}
  value='avg_carbs'
  title='Avg Daily Carbs'
  valueFormat='0'
  suffix=' g'
/>

## About This Data

This dashboard is powered by data from Nightscout, an open-source diabetes management platform. The data is processed through the DATAFLOW platform and visualized using Evidence.

Data updates hourly and includes:

- Glucose readings
- Insulin doses
- Carbohydrate intake
- Treatment events
