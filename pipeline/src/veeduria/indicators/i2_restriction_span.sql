-- I2, R11: contratos directos de la ventana de enero que terminan después de la restricción; ver docs/indicadores.md §3.
WITH windows AS (
    SELECT
        unnest($years) AS year,
        unnest($window_ends) AS window_end,
        unnest($reference_ends) AS reference_end
)
SELECT
    windows.year,
    -- El plazo pactado es la fecha de fin sin los días adicionados (ADR 0035).
    count(*) FILTER (
        WHERE CAST(contract.end_date AS DATE) - coalesce(contract.added_days, 0) > windows.reference_end
    ) AS count_numerator,
    count(*) AS count_denominator
FROM linked_contracts AS contract
JOIN windows
    -- R11: la ventana incluye el día en que termina.
    ON contract.signed_date >= make_date(windows.year, 1, 1)
    AND contract.signed_date < windows.window_end + INTERVAL 1 DAY
WHERE contract.direct_award
    AND contract.end_date IS NOT NULL
GROUP BY windows.year
ORDER BY windows.year
