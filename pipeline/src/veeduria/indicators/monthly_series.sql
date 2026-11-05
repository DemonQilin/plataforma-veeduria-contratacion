-- Serie mensual, R7, R12 y D3: contratos y valor por mes, modalidad y tipo; ver docs/reglas.md §7 y ADR 0040.
WITH base AS (
    SELECT
        CAST(date_trunc('month', contract.signed_date) AS DATE) AS month,
        contract.procurement_method,
        contract.contract_type,
        -- R7: el crédito público cuenta en los conteos y no en el valor.
        contract.is_value_eligible AND contract.initial_value IS NOT NULL AS has_value,
        contract.initial_value
    FROM linked_contracts AS contract
    -- R2 y R12: solo contratos firmados, hasta la fecha de corte.
    WHERE contract.signed_date IS NOT NULL
      AND CAST(contract.signed_date AS DATE) <= $cutoff_date
),
-- Las hojas (mes, modalidad, tipo) y sus totales: sin tipo, sin modalidad y solo el mes.
rolled AS (
    SELECT
        month,
        procurement_method,
        contract_type,
        count(*) AS contract_count,
        count(*) FILTER (WHERE has_value) AS value_sample_size,
        coalesce(sum(initial_value) FILTER (WHERE has_value), 0) AS value
    FROM base
    GROUP BY GROUPING SETS (
        (month, procurement_method, contract_type),
        (month, procurement_method),
        (month, contract_type),
        (month)
    )
),
combinations AS (
    SELECT DISTINCT procurement_method, contract_type FROM rolled
),
-- Todos los meses entre la primera firma y el mes de corte, para publicar los ceros.
spine AS (
    SELECT CAST(unnest(generate_series(
        first_month,
        CAST(date_trunc('month', CAST($cutoff_date AS DATE)) AS DATE),
        INTERVAL 1 MONTH
    )) AS DATE) AS month
    FROM (SELECT min(month) AS first_month FROM base)
    WHERE first_month IS NOT NULL
)
SELECT
    strftime(spine.month, '%Y-%m') AS period,
    combinations.procurement_method,
    combinations.contract_type,
    coalesce(rolled.contract_count, 0) AS contract_count,
    coalesce(rolled.value_sample_size, 0) AS value_sample_size,
    CAST(coalesce(rolled.value, 0) AS DOUBLE) AS value
FROM spine
CROSS JOIN combinations
LEFT JOIN rolled
    ON rolled.month = spine.month
   AND rolled.procurement_method IS NOT DISTINCT FROM combinations.procurement_method
   AND rolled.contract_type IS NOT DISTINCT FROM combinations.contract_type
ORDER BY period, procurement_method NULLS FIRST, contract_type NULLS FIRST
