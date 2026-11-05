-- I8, R7 y R17: proporción de la contratación directa firmada en enero y de febrero a junio; ver docs/indicadores.md §3.
WITH years AS (
    SELECT unnest($years) AS year
),
signed AS (
    SELECT
        years.year,
        month(contract.signed_date) = 1 AS is_january,
        month(contract.signed_date) BETWEEN 2 AND 6 AS is_february_june,
        -- R7: el crédito público cuenta en los conteos y no en el valor.
        contract.is_value_eligible AND contract.initial_value IS NOT NULL AS has_value,
        contract.initial_value
    FROM linked_contracts AS contract
    JOIN years ON year(contract.signed_date) = years.year
    WHERE contract.direct_award
),
by_year AS (
    SELECT
        year,
        count(*) AS count_denominator,
        count(*) FILTER (WHERE is_january) AS january_count,
        count(*) FILTER (WHERE is_february_june) AS february_june_count,
        coalesce(sum(initial_value) FILTER (WHERE has_value), 0) AS value_denominator,
        coalesce(sum(initial_value) FILTER (WHERE has_value AND is_january), 0) AS january_value,
        coalesce(sum(initial_value) FILTER (WHERE has_value AND is_february_june), 0) AS february_june_value,
        count(*) FILTER (WHERE has_value) AS value_sample_size
    FROM signed
    GROUP BY year
)
SELECT
    year,
    variant,
    CASE variant WHEN 'signed_january' THEN january_count ELSE february_june_count END AS count_numerator,
    count_denominator,
    CASE variant WHEN 'signed_january' THEN january_value ELSE february_june_value END AS value_numerator,
    value_denominator,
    value_sample_size
FROM by_year
CROSS JOIN (VALUES ('signed_january'), ('signed_february_june')) AS variants(variant)
ORDER BY year, variant
