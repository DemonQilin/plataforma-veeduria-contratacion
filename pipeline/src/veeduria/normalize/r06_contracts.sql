-- R1, R2 y R6: normaliza los contratos de SECOP II (entidad exacta, firma desde 2022, catálogos); ver docs/reglas.md.
CREATE OR REPLACE TABLE contracts AS
WITH raw AS MATERIALIZED (
    -- MATERIALIZED evita que DuckDB empuje los TRY_CAST al lector del CSV.
    SELECT *
    FROM read_csv($snapshot_path, all_varchar = true, header = true)
),
classified AS (
    SELECT
        unnest($method_texts) AS method_text,
        unnest($justification_texts) AS justification_text,
        unnest($type_texts) AS type_text,
        unnest($supplier_texts) AS supplier_text,
        unnest($method_codes) AS procurement_method,
        unnest($direct_awards) AS direct_award,
        unnest($competitives) AS competitive,
        unnest($contract_types) AS contract_type,
        unnest($supplier_types) AS supplier_type
)
SELECT
    raw.id_contrato AS contract_id,
    raw.referencia_del_contrato AS contract_reference,
    raw.proceso_de_compra AS procurement_process,
    classified.procurement_method,
    classified.direct_award,
    classified.competitive,
    raw.justificacion_modalidad_de AS method_justification,
    classified.contract_type,
    classified.supplier_type,
    TRY_CAST(raw.fecha_de_firma AS TIMESTAMP) AS signed_date,
    TRY_CAST(raw.fecha_de_inicio_del_contrato AS TIMESTAMP) AS start_date,
    TRY_CAST(raw.fecha_de_fin_del_contrato AS TIMESTAMP) AS end_date,
    TRY_CAST(raw.valor_del_contrato AS DECIMAL(18, 2)) AS contract_value,
    TRY_CAST(raw.dias_adicionados AS INTEGER) AS added_days,
    raw.estado_contrato AS contract_status,
    raw.codigo_de_categoria_principal AS main_category_code,
    raw.urlproceso AS process_url
FROM raw
JOIN classified
    ON coalesce(raw.modalidad_de_contratacion, '') = classified.method_text
    AND coalesce(raw.justificacion_modalidad_de, '') = classified.justification_text
    AND coalesce(raw.tipo_de_contrato, '') = classified.type_text
    AND coalesce(raw.tipodocproveedor, '') = classified.supplier_text
WHERE raw.nombre_entidad = $entity_name
    -- R2: las filas sin firma (o con firma ilegible) siguen aquí; R4 las excluye al consolidar.
    AND (TRY_CAST(raw.fecha_de_firma AS TIMESTAMP) IS NULL
        OR TRY_CAST(raw.fecha_de_firma AS TIMESTAMP) >= TIMESTAMP '2022-01-01 00:00:00')
