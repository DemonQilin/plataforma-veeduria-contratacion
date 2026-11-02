-- R6 y R17: normaliza el Plan Anual de Adquisiciones (modalidad según el catálogo, año, mes y valor numéricos); ver docs/reglas.md.
CREATE OR REPLACE TABLE procurement_plan AS
WITH raw AS MATERIALIZED (
    -- MATERIALIZED evita que DuckDB empuje los TRY_CAST al lector del CSV, que sí falla con «1,10E+11».
    SELECT *
    FROM read_csv($snapshot_path, all_varchar = true, header = true)
),
methods AS (
    SELECT
        unnest($raw_texts) AS raw_text,
        unnest($codes) AS code,
        unnest($direct_awards) AS direct_award,
        unnest($competitives) AS competitive
),
months(name, number) AS (
    VALUES
        ('enero', 1), ('febrero', 2), ('marzo', 3), ('abril', 4), ('mayo', 5), ('junio', 6),
        ('julio', 7), ('agosto', 8), ('septiembre', 9), ('octubre', 10), ('noviembre', 11),
        ('diciembre', 12)
)
SELECT
    TRY_CAST(TRY_CAST(raw.ano AS DOUBLE) AS INTEGER) AS year,
    months.number AS estimated_start_month,
    methods.code AS procurement_method,
    methods.direct_award AS direct_award,
    methods.competitive AS competitive,
    CASE
        WHEN regexp_full_match(raw.valor_total_estimado, '[0-9]+')
            THEN TRY_CAST(raw.valor_total_estimado AS BIGINT)
        -- Notación científica con coma decimal («1,10E+11»); «1,2611» no tiene lectura segura.
        WHEN regexp_full_match(raw.valor_total_estimado, '[0-9]+,[0-9]+E\+[0-9]+')
            THEN TRY_CAST(round(TRY_CAST(replace(raw.valor_total_estimado, ',', '.') AS DOUBLE)) AS BIGINT)
    END AS estimated_value,
    raw.unidad_de_contratacion AS department,
    raw.codigos_unspsc AS unspsc_codes
FROM raw
LEFT JOIN methods ON coalesce(raw.modalidad_seleccion, '') = methods.raw_text
LEFT JOIN months ON lower(trim(raw.fecha_estimada_inicio)) = months.name
