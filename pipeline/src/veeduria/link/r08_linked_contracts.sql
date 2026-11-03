-- R7, R8 y D3: contratos enriquecidos con el proceso y MEData; ver docs/reglas.md y ADR 0030.
CREATE OR REPLACE TABLE linked_contracts AS
WITH departments AS (
    SELECT
        unnest($department_texts) AS raw_text,
        unnest($department_codes) AS code
),
joined AS (
    SELECT
        contract.* EXCLUDE (final_value),
        process.response_count,
        process.unique_suppliers,
        process.awarded,
        process.base_price,
        process.awarded_value,
        process.published_date,
        process.response_deadline,
        medata.contract_reference IS NOT NULL AS in_medata,
        medata.total_addition_value,
        -- D3: el valor final es el de MEData si existe; si no, el de la versión más reciente de SECOP II.
        coalesce(medata.final_value, contract.final_value) AS final_value,
        medata_department.code AS medata_department,
        process_department.code AS process_department
    FROM canonical_contracts AS contract
    LEFT JOIN canonical_processes AS process
        ON contract.procurement_process = process.procurement_process
    LEFT JOIN medata_contracts AS medata
        ON contract.contract_reference = medata.contract_reference
    LEFT JOIN departments AS medata_department
        ON medata.department = medata_department.raw_text
    LEFT JOIN departments AS process_department
        ON process.department = process_department.raw_text
)
SELECT
    * EXCLUDE (medata_department, process_department),
    -- R8: MEData; si no, la unidad del proceso en SECOP II; si no, sin asignar.
    coalesce(medata_department, process_department, $unassigned_code) AS department,
    CASE
        WHEN medata_department IS NOT NULL THEN 'medata'
        WHEN process_department IS NOT NULL THEN 'secop'
        ELSE 'unassigned'
    END AS department_source,
    -- R7: el crédito público cuenta en los conteos y no en los indicadores de valor.
    contract_type IS DISTINCT FROM 'public_credit' AS is_value_eligible
FROM joined
ORDER BY contract_reference
