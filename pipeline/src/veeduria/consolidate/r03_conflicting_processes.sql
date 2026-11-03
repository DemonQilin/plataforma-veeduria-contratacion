-- R3: reporta las referencias cuyas versiones firmadas apuntan a procesos distintos; ver docs/reglas.md.
INSERT INTO quality_issues
WITH signed AS (
    SELECT
        contract_reference,
        procurement_process,
        row_number() OVER (
            PARTITION BY contract_reference ORDER BY signed_date ASC, contract_id ASC
        ) AS earliest_rank
    FROM contracts
    WHERE signed_date IS NOT NULL
),
kept AS (
    SELECT contract_reference, procurement_process AS kept_process
    FROM signed
    WHERE earliest_rank = 1
),
discarded AS (
    SELECT
        signed.contract_reference,
        string_agg(DISTINCT signed.procurement_process, ',' ORDER BY signed.procurement_process)
            AS discarded_processes
    FROM signed
    JOIN kept ON signed.contract_reference = kept.contract_reference
    WHERE signed.procurement_process IS DISTINCT FROM kept.kept_process
        AND signed.procurement_process IS NOT NULL
    GROUP BY signed.contract_reference
)
SELECT
    'R3' AS rule,
    discarded.contract_reference AS record_key,
    'kept=' || coalesce(kept.kept_process, '') || '; discarded=' || discarded.discarded_processes
        AS detail
FROM discarded
JOIN kept ON discarded.contract_reference = kept.contract_reference
ORDER BY record_key
