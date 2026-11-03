-- R8: reporta los textos de secretaría que el catálogo no reconoce y los contratos sin secretaría.
INSERT INTO quality_issues
SELECT rule, record_key, detail
FROM (
    SELECT 'R8' AS rule, unnest($unmapped_texts) AS record_key,
        'reason=unmapped_department_text' AS detail
    UNION ALL
    SELECT 'R8', contract_reference, 'reason=no_department'
    FROM linked_contracts
    WHERE department_source = 'unassigned'
)
ORDER BY detail, record_key
