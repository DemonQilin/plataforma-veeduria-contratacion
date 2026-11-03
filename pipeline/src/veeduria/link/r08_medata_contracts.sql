-- D3 y R8: un registro por contrato de MEData; ver docs/reglas.md y ADR 0030.
-- Secretaría, fecha, valores, duración y estado son constantes entre las líneas de un contrato.
-- Las líneas truncadas conservan la secretaría pero tienen los valores nulos, así que
-- max() las ignora sin pisar los valores de las líneas completas.
CREATE OR REPLACE TABLE medata_contracts AS
SELECT
    contract_reference,
    min(signed_date) AS signed_date,
    min(department) AS department,
    max(initial_value) AS initial_value,
    max(total_addition_value) AS total_addition_value,
    max(final_value) AS final_value,
    max(duration_days) AS duration_days,
    max(contract_status) AS contract_status,
    count(*) AS row_count,
    bool_and(truncated) AS truncated
FROM contract_execution
GROUP BY contract_reference
ORDER BY contract_reference
