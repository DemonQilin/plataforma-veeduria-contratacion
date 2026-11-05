-- I5, R7, R8 y D3: adiciones de los contratos que están en MEData, por año de firma; ver docs/indicadores.md §2 y ADR 0044.
WITH base AS (
    SELECT
        -- El periodo sigue la fecha de firma de MEData, no la de SECOP II: el conjunto es de MEData.
        year(medata.signed_date) AS year,
        contract.department,
        medata.total_addition_value,
        medata.initial_value,
        medata.total_addition_value > 0 AS has_addition,
        -- R7: el crédito público cuenta en los conteos y no en el valor.
        contract.is_value_eligible AND medata.initial_value > 0 AS has_value,
        -- Cerca del tope legal de adiciones (50 %): desde el 45 % del valor inicial de MEData.
        medata.total_addition_value > 0 AND medata.initial_value > 0
            AND medata.total_addition_value >= 0.45 * medata.initial_value AS is_near_cap,
        medata.total_addition_value > 0 AND medata.initial_value > 0 AS can_measure_cap
    FROM linked_contracts AS contract
    JOIN medata_contracts AS medata
        ON contract.contract_reference = medata.contract_reference
    WHERE contract.in_medata
        AND medata.signed_date IS NOT NULL
        -- Un monto de adiciones no informado no es «sin adición»: el contrato sale del denominador.
        AND medata.total_addition_value IS NOT NULL
),
scoped AS (
    SELECT year, 'district' AS level, CAST(NULL AS VARCHAR) AS department,
           total_addition_value, initial_value, has_addition, has_value, is_near_cap, can_measure_cap
    FROM base
    UNION ALL
    -- R8: la secretaría "sin asignar" también tiene celda, para que las secretarías sumen al Distrito.
    SELECT year, 'department' AS level, department,
           total_addition_value, initial_value, has_addition, has_value, is_near_cap, can_measure_cap
    FROM base
)
SELECT
    year,
    level,
    department,
    count(*) FILTER (WHERE has_addition) AS count_numerator,
    count(*) AS count_denominator,
    coalesce(sum(total_addition_value) FILTER (WHERE has_value), 0) AS value_numerator,
    coalesce(sum(initial_value) FILTER (WHERE has_value), 0) AS value_denominator,
    count(*) FILTER (WHERE has_value) AS value_sample_size,
    count(*) FILTER (WHERE is_near_cap) AS cap_numerator,
    count(*) FILTER (WHERE can_measure_cap) AS cap_denominator
FROM scoped
GROUP BY year, level, department
ORDER BY year, level, department NULLS FIRST
