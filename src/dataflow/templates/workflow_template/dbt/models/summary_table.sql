/*
    Summary table with aggregated metrics.
    This is a template for an aggregation model.
*/

WITH staged_data AS (
    SELECT * FROM {{ ref('staged_data') }}
)

SELECT
    DATE_TRUNC('day', timestamp) AS date,
    COUNT(*) AS record_count,

    -- Type counts
    COUNT(CASE WHEN type = 'type1' THEN 1 END) AS type1_count,
    COUNT(CASE WHEN type = 'type2' THEN 1 END) AS type2_count,

    -- Value metrics
    AVG(value) AS average_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,

    -- Metadata
    CURRENT_TIMESTAMP() AS processed_at
FROM staged_data
GROUP BY DATE_TRUNC('day', timestamp)
