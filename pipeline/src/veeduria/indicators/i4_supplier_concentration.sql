-- I4, R7, R8, R14 y D3: concentración del valor en los 5 proveedores con más valor; ver docs/indicadores.md §1 y ADR 0045.
WITH linked AS (
    SELECT
        contract.contract_reference,
        year(contract.signed_date) AS year,
        contract.department,
        supplier.supplier_id,
        contract.initial_value,
        -- Un proveedor por contrato: el de la versión canónica y, si no, el de menor NIT.
        row_number() OVER (
            PARTITION BY contract.contract_reference
            ORDER BY (supplier.contract_id = contract.contract_id) DESC, supplier.supplier_id
        ) AS supplier_rank
    FROM suppliers AS supplier
    JOIN contracts AS version
        ON supplier.contract_id = version.contract_id
    JOIN linked_contracts AS contract
        ON version.contract_reference = contract.contract_reference
    -- R7: sin crédito público ni contratos sin valor. R14: `suppliers` solo trae personas jurídicas.
    WHERE contract.signed_date IS NOT NULL
        AND contract.is_value_eligible
        AND contract.initial_value IS NOT NULL
),
base AS (
    SELECT year, department, supplier_id, initial_value
    FROM linked
    WHERE supplier_rank = 1
),
scoped AS (
    SELECT year, 'district' AS level, CAST(NULL AS VARCHAR) AS department, supplier_id, initial_value
    FROM base
    UNION ALL
    -- R8: la secretaría "sin asignar" también tiene celda, para que las secretarías sumen al Distrito.
    SELECT year, 'department' AS level, department, supplier_id, initial_value
    FROM base
),
by_supplier AS (
    SELECT
        year,
        level,
        department,
        supplier_id,
        sum(initial_value) AS supplier_value,
        count(*) AS supplier_contracts
    FROM scoped
    GROUP BY year, level, department, supplier_id
),
ranked AS (
    SELECT
        *,
        row_number() OVER (
            PARTITION BY year, level, department
            ORDER BY supplier_value DESC, supplier_id
        ) AS value_rank
    FROM by_supplier
)
SELECT
    year,
    level,
    department,
    sum(supplier_value) FILTER (WHERE value_rank <= $top_suppliers) AS top_value,
    sum(supplier_value) AS total_value,
    sum(supplier_contracts) AS sample_size,
    count(*) AS supplier_count
FROM ranked
GROUP BY year, level, department
ORDER BY year, level, department NULLS FIRST
