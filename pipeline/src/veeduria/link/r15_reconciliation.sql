-- R15: conciliación mensual SECOP–MEData; ver docs/reglas.md y ADR 0031.
-- El periodo común va del primer al último mes de MEData. El mes de un contrato sale de la fecha
-- de firma de SECOP II (la canónica); la de MEData solo se usa si el contrato no está en SECOP II.
CREATE OR REPLACE TABLE reconciliation AS
WITH contracts AS (
    SELECT
        coalesce(secop.contract_reference, medata.contract_reference) AS contract_reference,
        date_trunc('month', coalesce(secop.signed_date, medata.signed_date))::DATE AS month,
        secop.contract_reference IS NOT NULL AS in_secop,
        medata.contract_reference IS NOT NULL AS in_medata
    FROM canonical_contracts AS secop
    FULL JOIN medata_contracts AS medata
        ON secop.contract_reference = medata.contract_reference
),
period AS (
    SELECT unnest(generate_series(
        date_trunc('month', min(signed_date))::DATE,
        date_trunc('month', max(signed_date))::DATE,
        INTERVAL 1 MONTH
    ))::DATE AS month
    FROM medata_contracts
),
counts AS (
    SELECT
        period.month,
        count(*) FILTER (WHERE contracts.in_secop) AS secop_count,
        count(*) FILTER (WHERE contracts.in_medata) AS medata_count,
        count(*) FILTER (WHERE contracts.in_secop AND contracts.in_medata) AS shared_count,
        count(contracts.contract_reference) AS union_count
    FROM period
    LEFT JOIN contracts ON contracts.month = period.month
    GROUP BY period.month
)
SELECT
    month,
    secop_count,
    medata_count,
    shared_count,
    union_count,
    round(shared_count / nullif(union_count, 0), 4)::DECIMAL(5, 4) AS shared_share,
    round(shared_count / nullif(secop_count, 0), 4)::DECIMAL(5, 4) AS secop_coverage,
    round(shared_count / nullif(medata_count, 0), 4)::DECIMAL(5, 4) AS medata_coverage,
    -- Se compara con conteos, no con el porcentaje redondeado: 4 de 5 es 80 % y no se advierte.
    shared_count < $threshold * union_count AS below_threshold
FROM counts
ORDER BY month
