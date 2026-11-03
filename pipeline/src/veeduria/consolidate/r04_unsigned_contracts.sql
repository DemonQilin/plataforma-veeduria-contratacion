-- R4: reporta los contratos sin fecha de firma que la consolidación excluye; ver docs/reglas.md.
INSERT INTO quality_issues
SELECT
    'R4' AS rule,
    contract_id AS record_key,
    'contract_reference=' || coalesce(contract_reference, '') AS detail
FROM contracts
WHERE signed_date IS NULL
ORDER BY record_key
