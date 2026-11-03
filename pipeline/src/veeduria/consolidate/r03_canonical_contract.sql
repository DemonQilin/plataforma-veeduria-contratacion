-- R3 y R4: un contrato por referencia a partir de las versiones firmadas; ver docs/reglas.md.
CREATE OR REPLACE TABLE canonical_contracts AS
WITH ranked AS (
    SELECT
        *,
        -- R4: las filas sin fecha de firma no entran.
        -- Se compara la marca de tiempo completa; contract_id solo desempata.
        row_number() OVER (
            PARTITION BY contract_reference ORDER BY signed_date ASC, contract_id ASC
        ) AS earliest_rank,
        row_number() OVER (
            PARTITION BY contract_reference ORDER BY signed_date DESC, contract_id DESC
        ) AS latest_rank,
        count(*) OVER (PARTITION BY contract_reference) AS version_count
    FROM contracts
    WHERE signed_date IS NOT NULL
)
SELECT
    earliest.contract_reference,
    earliest.contract_id,
    earliest.procurement_process,
    earliest.procurement_method,
    earliest.direct_award,
    earliest.competitive,
    earliest.method_justification,
    earliest.contract_type,
    earliest.supplier_type,
    earliest.signed_date,
    earliest.start_date,
    latest.end_date,
    earliest.contract_value AS initial_value,
    -- D3 (parte SECOP II): el valor final es el de la versión más reciente; MEData lo reemplaza al cruzar.
    latest.contract_value AS final_value,
    latest.added_days,
    latest.contract_status,
    earliest.main_category_code,
    earliest.process_url,
    earliest.version_count
FROM ranked AS earliest
JOIN ranked AS latest
    ON earliest.contract_reference = latest.contract_reference
WHERE earliest.earliest_rank = 1
    AND latest.latest_rank = 1
ORDER BY earliest.contract_reference
