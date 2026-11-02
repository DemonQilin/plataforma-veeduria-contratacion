-- R1 y R6: normaliza los procesos de SECOP II (entidad exacta, catálogos, sin filtro de fecha); ver docs/reglas.md.
CREATE OR REPLACE TABLE procurement_processes AS
WITH raw AS MATERIALIZED (
    -- MATERIALIZED evita que DuckDB empuje los TRY_CAST al lector del CSV.
    SELECT *
    FROM read_csv($snapshot_path, all_varchar = true, header = true)
),
classified AS (
    SELECT
        unnest($method_texts) AS method_text,
        unnest($type_texts) AS type_text,
        unnest($method_codes) AS procurement_method,
        unnest($direct_awards) AS direct_award,
        unnest($competitives) AS competitive,
        unnest($contract_types) AS contract_type
)
SELECT
    raw.id_del_portafolio AS procurement_process,
    raw.id_del_proceso AS process_id,
    classified.procurement_method,
    classified.direct_award,
    classified.competitive,
    classified.contract_type,
    TRY_CAST(raw.fecha_de_publicacion_del AS TIMESTAMP) AS published_date,
    TRY_CAST(raw.fecha_de_recepcion_de AS TIMESTAMP) AS response_deadline,
    TRY_CAST(raw.precio_base AS DECIMAL(18, 2)) AS base_price,
    TRY_CAST(raw.valor_total_adjudicacion AS DECIMAL(18, 2)) AS awarded_value,
    TRY_CAST(raw.respuestas_al_procedimiento AS INTEGER) AS response_count,
    TRY_CAST(raw.proveedores_unicos_con AS INTEGER) AS unique_suppliers,
    CASE raw.adjudicado WHEN 'Si' THEN TRUE WHEN 'No' THEN FALSE END AS awarded,
    raw.nombre_de_la_unidad_de AS department
FROM raw
JOIN classified
    ON coalesce(raw.modalidad_de_contratacion, '') = classified.method_text
    AND coalesce(raw.tipo_de_contrato, '') = classified.type_text
WHERE raw.entidad = $entity_name
