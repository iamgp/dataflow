/*
    Staged data with basic type conversions.
    This is a template for a staging model.
*/

WITH source_data AS (
    SELECT * FROM {{ source('raw_data', 'raw_workflow_data') }}
)

SELECT
    id,
    TIMESTAMP '{{ timestamp }}' AS timestamp,
    CAST(value AS FLOAT) AS value,
    type,

    -- Add any derived fields
    CASE
        WHEN type = 'type1' THEN 'Category A'
        WHEN type = 'type2' THEN 'Category B'
        ELSE 'Other'
    END AS category,

    -- Add processing metadata
    CURRENT_TIMESTAMP() AS processed_at
FROM source_data
