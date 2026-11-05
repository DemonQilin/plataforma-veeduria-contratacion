-- I8 y R17: proporción de la contratación directa planeada en enero y de febrero a junio; ver docs/indicadores.md §3.
WITH planned AS (
    SELECT
        year,
        estimated_start_month BETWEEN 2 AND 6 AS is_february_june,
        estimated_start_month = 1 AS is_january,
        estimated_value
    FROM procurement_plan
    WHERE direct_award AND year IS NOT NULL AND estimated_start_month IS NOT NULL
),
by_year AS (
    SELECT
        year,
        count(*) AS count_denominator,
        count(*) FILTER (WHERE is_january) AS january_count,
        count(*) FILTER (WHERE is_february_june) AS february_june_count,
        -- Las líneas sin valor quedan fuera de la medida por valor y de su tamaño de muestra.
        coalesce(sum(estimated_value), 0) AS value_denominator,
        coalesce(sum(estimated_value) FILTER (WHERE is_january), 0) AS january_value,
        coalesce(sum(estimated_value) FILTER (WHERE is_february_june), 0) AS february_june_value,
        count(estimated_value) AS value_sample_size
    FROM planned
    GROUP BY year
)
SELECT
    year,
    variant,
    CASE variant WHEN 'planned_january' THEN january_count ELSE february_june_count END AS count_numerator,
    count_denominator,
    CASE variant WHEN 'planned_january' THEN january_value ELSE february_june_value END AS value_numerator,
    value_denominator,
    value_sample_size
FROM by_year
CROSS JOIN (VALUES ('planned_january'), ('planned_february_june')) AS variants(variant)
ORDER BY year, variant
