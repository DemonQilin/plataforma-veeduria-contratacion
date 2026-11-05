-- I1, R6, R7, R8, D1 y D2: proporción de la contratación directa por año; ver docs/indicadores.md §1 y ADR 0039.
WITH base AS (
    SELECT
        year(contract.signed_date) AS year,
        contract.department,
        -- R6 y D1: la bandera `direct_award` ya incluye la contratación directa con ofertas.
        coalesce(contract.direct_award, false) AS is_direct,
        -- D2: la proporción no competitiva suma el régimen especial a la directa.
        coalesce(contract.direct_award, false)
            OR contract.procurement_method = 'special_regime' AS is_non_competitive,
        -- R7: el crédito público cuenta en los conteos y no en el valor.
        contract.is_value_eligible AND contract.initial_value IS NOT NULL AS has_value,
        contract.initial_value
    FROM linked_contracts AS contract
    WHERE contract.signed_date IS NOT NULL
),
scoped AS (
    SELECT year, 'district' AS level, CAST(NULL AS VARCHAR) AS department,
           is_direct, is_non_competitive, has_value, initial_value
    FROM base
    UNION ALL
    -- R8: la secretaría "sin asignar" también tiene celda, para que las secretarías sumen al Distrito.
    SELECT year, 'department' AS level, department,
           is_direct, is_non_competitive, has_value, initial_value
    FROM base
),
aggregated AS (
    SELECT
        year,
        level,
        department,
        count(*) AS count_denominator,
        count(*) FILTER (WHERE is_direct) AS direct_count,
        count(*) FILTER (WHERE is_non_competitive) AS non_competitive_count,
        coalesce(sum(initial_value) FILTER (WHERE has_value), 0) AS value_denominator,
        coalesce(sum(initial_value) FILTER (WHERE has_value AND is_direct), 0) AS direct_value,
        coalesce(sum(initial_value) FILTER (WHERE has_value AND is_non_competitive), 0) AS non_competitive_value,
        count(*) FILTER (WHERE has_value) AS value_sample_size
    FROM scoped
    GROUP BY year, level, department
)
SELECT
    year,
    level,
    department,
    variant,
    CASE variant WHEN 'non_competitive' THEN non_competitive_count ELSE direct_count END AS count_numerator,
    count_denominator,
    CASE variant WHEN 'non_competitive' THEN non_competitive_value ELSE direct_value END AS value_numerator,
    value_denominator,
    value_sample_size
FROM aggregated
CROSS JOIN (VALUES (CAST(NULL AS VARCHAR)), ('non_competitive')) AS variants(variant)
ORDER BY year, level, department NULLS FIRST, variant NULLS FIRST
