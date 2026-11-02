# 0023. Normalización de Contratos: una fila por `id_contrato`, sin firma se conserva

- **Estado:** Aceptada
- **Fecha:** 2026-11-02
- **Fuente:** [docs/reglas.md](../reglas.md#4-reglas) (R1, R2, R4, R6)

## Contexto

La copia de Contratos de SECOP II tiene 7.468 filas, una por `id_contrato`, con 7.428 referencias distintas. Hay que decidir qué hace la normalización y qué deja a la consolidación (R3, R4).

## Decisión

- **R1 se aplica de nuevo con el nombre exacto** (`nombre_entidad`), aunque la extracción ya filtra, para que la regla se pruebe en la normalización. La columna no pasa a la tabla, porque queda constante.
- **R2 solo aplica el límite inferior** (firma desde 2022-01-01). El superior no filtra nada: la fecha de corte es la firma más reciente de la misma copia (R12).
- **Las filas sin firma (o con firma ilegible) se conservan** con `signed_date` nulo. Si se quitaran aquí, R4 no tendría efecto ni se vería en el reporte de calidad. La copia actual no tiene ninguna.
- **No se deduplica.** Una fila por `id_contrato`; R3 elige el contrato canónico en la consolidación.
- **Tipos:** fechas como `TIMESTAMP` (R3 compara la marca de tiempo completa), valor como `DECIMAL(18,2)` (llega con hasta dos decimales) y días adicionados como `INTEGER`. Lo que no se pueda leer queda en `NULL`.
- **Los catálogos (R6) se aplican en Python** sobre las combinaciones distintas de modalidad, justificación, tipo y tipo de documento, y llegan al SQL como listas paralelas (ADR 0021, ADR 0022).

## Consecuencias

- `contracts` queda con 17 columnas en inglés.
- Las pruebas golden fijan 7.468 filas, ninguna modalidad en `other`, 1.446 interadministrativos, 4.508 / 2.875 / 85 proveedores jurídicos / naturales / no definidos y 723 referencias de contratación directa firmadas en enero de 2022.
