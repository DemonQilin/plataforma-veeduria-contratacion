-- R9: procesos válidos para oferente único (competitivos, adjudicados, desde R2 hasta el corte R12); ver docs/reglas.md y ADR 0043.
CREATE OR REPLACE TABLE single_bidder_processes AS
WITH classified AS (
    -- R8: la unidad del proceso se traduce con el catálogo de secretarías.
    SELECT
        unnest(CAST($department_texts AS VARCHAR[])) AS department_text,
        unnest(CAST($department_codes AS VARCHAR[])) AS department_code
)
SELECT
    process.procurement_process,
    year(process.published_date) AS year,
    coalesce(classified.department_code, $unassigned) AS department,
    process.unique_suppliers,
    -- R9: cero oferentes, o ninguno reportado, es un error de datos.
    coalesce(process.unique_suppliers, 0) < 1 AS is_excluded
FROM canonical_processes AS process
LEFT JOIN classified ON process.department = classified.department_text
WHERE process.competitive
    AND process.awarded
    AND process.published_date >= DATE '2022-01-01'
    AND process.published_date::DATE <= (SELECT max(signed_date)::DATE FROM canonical_contracts)
ORDER BY process.procurement_process
