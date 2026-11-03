-- R5: un proceso por portafolio; oferentes en máximo, adjudicado si alguna fila lo está; ver docs/reglas.md.
CREATE OR REPLACE TABLE canonical_processes AS
WITH ranked AS (
    SELECT
        *,
        -- Los campos descriptivos salen de la fila con la primera publicación.
        row_number() OVER (
            PARTITION BY procurement_process
            ORDER BY published_date ASC NULLS LAST, process_id ASC NULLS LAST
        ) AS earliest_rank
    FROM procurement_processes
    WHERE procurement_process IS NOT NULL
),
aggregated AS (
    SELECT
        procurement_process,
        max(response_count) AS response_count,
        max(unique_suppliers) AS unique_suppliers,
        -- Las filas repetidas no se suman: se toma el máximo.
        max(base_price) AS base_price,
        max(awarded_value) AS awarded_value,
        bool_or(awarded) AS awarded,
        count(*) AS row_count
    FROM ranked
    GROUP BY procurement_process
)
SELECT
    earliest.procurement_process,
    earliest.process_id,
    earliest.procurement_method,
    earliest.direct_award,
    earliest.competitive,
    earliest.contract_type,
    earliest.published_date,
    earliest.response_deadline,
    aggregated.base_price,
    aggregated.awarded_value,
    aggregated.response_count,
    aggregated.unique_suppliers,
    aggregated.awarded,
    earliest.department,
    aggregated.row_count
FROM ranked AS earliest
JOIN aggregated ON earliest.procurement_process = aggregated.procurement_process
WHERE earliest.earliest_rank = 1
ORDER BY earliest.procurement_process
