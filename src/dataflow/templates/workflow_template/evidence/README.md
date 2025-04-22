# Evidence Dashboards

This directory contains Evidence dashboards for visualizing the workflow data.

## Structure

- `index.md` - Main dashboard page
- `components/` - Reusable chart components
- `pages/` - Additional dashboard pages

## Usage

Dashboards should follow Evidence best practices:

- Organize related visualizations on the same page
- Use clear titles and descriptions for each chart
- Include filters for interactive exploration
- Document any special considerations for interpreting the data

## Example Pages

For this workflow, we recommend implementing the following pages:

1. `index.md` - Main dashboard with key metrics overview
2. `details.md` - Detailed exploration of specific metrics
3. `trends.md` - Time-based analysis and trends

## Development

To preview dashboards locally, run the Evidence development server:

```
cd integrations/evidence
npm run dev
```

The dashboards will be available at http://localhost:9000.
