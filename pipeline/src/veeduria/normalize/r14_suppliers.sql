-- R14 (I4): normaliza los proveedores de SECOP II (NIT sin dígito de verificación y un nombre
-- por NIT); ver docs/reglas.md.
CREATE OR REPLACE TABLE suppliers AS
WITH raw AS MATERIALIZED (
    SELECT *
    FROM read_csv($snapshot_path, all_varchar = true, header = true)
),
document_ids AS (
    SELECT
        unnest($documents) AS document,
        unnest($document_ids) AS supplier_id
),
names AS (
    SELECT
        unnest($supplier_ids) AS supplier_id,
        unnest($supplier_names) AS supplier_name
)
SELECT
    raw.id_contrato AS contract_id,
    document_ids.supplier_id,
    names.supplier_name
FROM raw
JOIN document_ids ON coalesce(raw.documento_proveedor, '') = document_ids.document
JOIN names ON document_ids.supplier_id = names.supplier_id
