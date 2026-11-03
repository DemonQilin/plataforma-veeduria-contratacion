-- R6 (I5): normaliza las adiciones de SECOP II con el catálogo de tipos; ver docs/reglas.md.
CREATE OR REPLACE TABLE additions AS
WITH raw AS MATERIALIZED (
    -- MATERIALIZED evita que DuckDB empuje los TRY_CAST al lector del CSV.
    SELECT *
    FROM read_csv($snapshot_path, all_varchar = true, header = true)
),
classified AS (
    SELECT
        unnest($type_texts) AS type_text,
        unnest($addition_types) AS addition_type,
        unnest($value_flags) AS is_value_addition
)
SELECT
    raw.id_contrato AS contract_id,
    classified.addition_type,
    classified.is_value_addition,
    TRY_CAST(raw.fecharegistro AS TIMESTAMP) AS registered_date
FROM raw
JOIN classified ON coalesce(raw.tipo, '') = classified.type_text
