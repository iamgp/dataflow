# Nightscout Evidence Dashboards

This directory contains Evidence dashboards for visualizing Nightscout data.

## Dashboards

- `index.md` - Main landing page with summary metrics and navigation
- `dashboard.md` - Primary dashboard with glucose trends and daily stats
- `hourly_patterns.md` - Time-based analysis for pattern identification

## Data Source

These dashboards rely on the following DBT models:

- `readings` - Processed glucose readings
- `treatments` - Processed treatment events
- `daily_summary` - Daily aggregated metrics

## Adding New Visualizations

To add a new visualization:

1. Create a new `.md` file with the Evidence Markdown format
2. Define SQL queries to fetch relevant data
3. Add visualizations using Evidence components
4. Link to the new dashboard from `index.md`

## Development

To develop and test locally:

```bash
cd integrations/evidence
npm run dev
```

This will launch the Evidence development server.

## Deployment

Evidence dashboards are automatically built and deployed when changes are pushed to the main branch. You can also manually trigger a build:

```bash
dataflow evidence build
```
