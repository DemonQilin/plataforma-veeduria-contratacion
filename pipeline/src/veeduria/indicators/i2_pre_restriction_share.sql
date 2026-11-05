-- I2, R7, R11 y R12: concentración pre-restricción de la contratación directa; ver docs/indicadores.md §3.
WITH windows AS (
    SELECT
        unnest($years) AS year,
        unnest($window_ends) AS window_end,
        unnest($denominator_ends) AS denominator_end
),
scoped AS (
    SELECT
        windows.year,
        coalesce(contract.contract_type = 'service_contract', false) AS is_service,
        -- R11: la ventana incluye el día en que termina.
        contract.signed_date < windows.window_end + INTERVAL 1 DAY AS is_pre_restriction,
        -- R7: el crédito público cuenta en los conteos y no en el valor.
        contract.is_value_eligible AND contract.initial_value IS NOT NULL AS has_value,
        contract.initial_value
    FROM linked_contracts AS contract
    JOIN windows
        -- R12: tramo común, del 1 de enero al día y mes de la fecha de corte.
        ON contract.signed_date >= make_date(windows.year, 1, 1)
        AND contract.signed_date < windows.denominator_end + INTERVAL 1 DAY
    WHERE contract.direct_award
)
SELECT
    year,
    CASE
        WHEN grouping(is_service) = 1 THEN NULL
        WHEN is_service THEN 'service_contract'
        ELSE 'non_service_contract'
    END AS variant,
    count(*) FILTER (WHERE is_pre_restriction) AS count_numerator,
    count(*) AS count_denominator,
    coalesce(sum(initial_value) FILTER (WHERE has_value AND is_pre_restriction), 0) AS value_numerator,
    coalesce(sum(initial_value) FILTER (WHERE has_value), 0) AS value_denominator,
    count(*) FILTER (WHERE has_value) AS value_sample_size
FROM scoped
GROUP BY GROUPING SETS ((year), (year, is_service))
ORDER BY year, variant NULLS FIRST
