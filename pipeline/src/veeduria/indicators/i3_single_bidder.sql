-- I3, R5, R8 y R9: proporción de procesos competitivos adjudicados con un solo oferente por año; ver docs/indicadores.md §2 y ADR 0043.
WITH valid AS (
    SELECT year, department, unique_suppliers = 1 AS is_single_bidder
    FROM single_bidder_processes
    WHERE NOT is_excluded
),
scoped AS (
    SELECT year, 'district' AS level, CAST(NULL AS VARCHAR) AS department, is_single_bidder
    FROM valid
    UNION ALL
    -- R8: la secretaría "sin asignar" también tiene celda, para que las secretarías sumen al Distrito.
    SELECT year, 'department' AS level, department, is_single_bidder
    FROM valid
)
SELECT
    year,
    level,
    department,
    count(*) FILTER (WHERE is_single_bidder) AS numerator,
    count(*) AS denominator
FROM scoped
GROUP BY year, level, department
ORDER BY year, level, department NULLS FIRST
