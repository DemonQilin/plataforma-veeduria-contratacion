# 0024. Normalización de Procesos: una fila por fila de la copia, sin filtro de fecha

- **Estado:** Aceptada
- **Fecha:** 2026-11-02
- **Fuente:** [docs/reglas.md](../reglas.md#4-reglas) (R1, R5, R6)

## Contexto

La copia de Procesos de SECOP II tiene 23.450 filas, 17.260 portafolios y 4.061 duplicados exactos que se conservan (ADR 0016). Hay que decidir qué hace la normalización y qué deja a la consolidación (R5).

## Decisión

- **R1 se aplica de nuevo con el nombre exacto** (`entidad`), igual que en Contratos (ADR 0023). La columna no pasa a la tabla.
- **Sin filtro de fecha.** R2 es una regla de contratos: un contrato firmado en 2022 puede venir de un proceso publicado antes (`docs/fuentes.md`).
- **No se deduplica.** Una fila por fila de la copia; R5 consolida por portafolio en la tarea 7.
- **Tipos:** fechas como `TIMESTAMP`, valores como `DECIMAL(18,2)`, conteos como `INTEGER`. Lo que no se pueda leer queda en `NULL`.
- **`adjudicado` pasa a booleano:** `Si` es verdadero, `No` es falso y cualquier otro valor queda en `NULL`.
- **Los ceros se conservan** (cero oferentes, precio base cero): R9 los excluye en el indicador, no aquí.
- **Los catálogos (R6) se aplican en Python** sobre las combinaciones distintas de modalidad y tipo, y llegan al SQL como listas paralelas (ADR 0021, ADR 0022). Procesos no trae justificación de la modalidad, así que el tipo nunca sale `interadministrative` en esta tabla.

## Consecuencias

- `procurement_processes` queda con 14 columnas en inglés.
- Las pruebas golden fijan 23.450 filas, 17.260 portafolios, 1.129 filas en `other` (ninguna adjudicada), 15.509 de contratación directa y 7.305 adjudicadas.
- La consolidación debe decidir cómo se resuelve `adjudicado` en los 1.169 portafolios que mezclan valores (`docs/bitacora.md`).
