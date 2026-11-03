-- R2 y R6: normaliza MEData · Ejecución (codificación reparada, modalidad según el catálogo, fecha desde 2022, valores numéricos); ver docs/reglas.md y ADR 0010.
CREATE OR REPLACE TABLE contract_execution AS
WITH raw AS MATERIALIZED (
    -- MATERIALIZED evita que DuckDB empuje los TRY_CAST al lector del CSV.
    SELECT *
    FROM read_csv($snapshot_path, all_varchar = true, header = true)
),
texts AS (
    SELECT
        unnest($raw_texts) AS raw_text,
        unnest($fixed_texts) AS fixed_text,
        unnest($codes) AS code,
        unnest($direct_awards) AS direct_award,
        unnest($competitives) AS competitive
),
parsed AS (
    SELECT
        raw.*,
        CAST(try_strptime(raw.fecha_contrato, '%d/%m/%Y') AS DATE) AS signed_date
    FROM raw
)
SELECT
    parsed.contrato AS contract_reference,
    parsed.signed_date,
    method.code AS procurement_method,
    method.direct_award,
    method.competitive,
    nullif(justification.fixed_text, '') AS method_justification,
    nullif(department.fixed_text, '') AS department,
    nullif(program.fixed_text, '') AS program,
    TRY_CAST(replace(replace(parsed.valor_inicial_contrato, '.', ''), ',', '.') AS DECIMAL(18, 2)) AS initial_value,
    TRY_CAST(replace(replace(parsed.valor_total_adic_contrato, '.', ''), ',', '.') AS DECIMAL(18, 2)) AS total_addition_value,
    TRY_CAST(replace(replace(parsed.valor_fin_contrato, '.', ''), ',', '.') AS DECIMAL(18, 2)) AS final_value,
    TRY_CAST(parsed.duracion_en_dias AS INTEGER) AS duration_days,
    nullif(status.fixed_text, '') AS contract_status,
    TRY_CAST(TRY_CAST(parsed.ano AS DOUBLE) AS INTEGER) AS year,
    parsed.truncated = 'true' AS truncated
FROM parsed
LEFT JOIN texts AS method ON coalesce(parsed.modalidad, '') = method.raw_text
LEFT JOIN texts AS justification ON coalesce(parsed.causal, '') = justification.raw_text
LEFT JOIN texts AS department ON coalesce(parsed.nombre_secretaria, '') = department.raw_text
LEFT JOIN texts AS program ON coalesce(parsed.nombre_programa, '') = program.raw_text
LEFT JOIN texts AS status ON coalesce(parsed.estado, '') = status.raw_text
-- R2: las filas sin fecha legible se conservan; R4 las excluye al consolidar.
WHERE parsed.signed_date IS NULL OR parsed.signed_date >= DATE '2022-01-01'
