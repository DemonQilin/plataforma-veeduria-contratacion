# 0029. Consolidación de contratos y procesos con una tabla de hallazgos de calidad

- **Estado:** Aceptada
- **Fecha:** 2026-11-03
- **Fuente:** [docs/reglas.md](../reglas.md#4-reglas) (R3, R4, R5, D3), [ADR 0011](0011-duckdb-una-regla-por-archivo.md), [ADR 0023](0023-normalizacion-de-contratos-sin-consolidar.md), [ADR 0024](0024-normalizacion-de-procesos-sin-consolidar.md)

## Contexto

Los normalizadores dejan una fila por fila de la copia: 7.468 de Contratos (7.428 referencias) y 23.450 de Procesos (17.260 portafolios). R3, R4 y R5 no dicen qué hacer cuando las filas de una misma referencia apuntan a procesos distintos (6 casos) ni cuando un portafolio mezcla filas adjudicadas y no adjudicadas (1.169 casos).

## Decisión

- **Contratos** (`canonical_contracts`): una fila por `contract_reference`. R4 excluye las filas sin firma antes de elegir. La primera versión se decide por la marca de tiempo completa de la firma y, si coincide, por `contract_id`.
  - De la primera versión salen la firma, el valor inicial y los atributos del contrato (proceso, modalidad, tipo, proveedor).
  - De la más reciente salen el valor final, el estado, los días adicionados y la fecha de fin.
  - **Si las versiones apuntan a procesos distintos, gana el proceso de la primera firma.** Es la decisión del 2 nov; la referencia queda en el reporte.
- **D3 se aplica solo en su parte SECOP II.** `final_value` es el valor de la versión más reciente; el valor de MEData lo reemplaza al cruzar (tarea 8).
- **Procesos** (`canonical_processes`): una fila por `procurement_process`.
  - `response_count` y `unique_suppliers` son el máximo entre las filas (R5).
  - **`awarded` es verdadero si alguna fila lo es**, falso si hay alguna fila con valor y ninguna verdadera, y nulo si todas son nulas.
  - `base_price` y `awarded_value` son el máximo, no la suma, porque hay 4.061 filas exactamente repetidas.
  - Los demás campos, incluido `process_id`, salen de la fila con la primera fecha de publicación. Es un supuesto: un portafolio puede tener varios `process_id`, y R9 no los usa.
  - Las filas sin portafolio no se consolidan.
- **`quality_issues(rule, record_key, detail)`** es una tabla compartida y la primera de calidad del proyecto. R3 anota una fila por referencia con procesos distintos (`kept=…; discarded=…`) y R4 una por `contract_id` sin firma. Cada regla borra sus propias filas antes de insertar, así que se puede repetir sin duplicar.
- Cada regla vive en su archivo SQL (`r03_canonical_contract.sql`, `r03_conflicting_processes.sql`, `r04_unsigned_contracts.sql`, `r05_canonical_process.sql`).

## Consecuencias

- Con la copia actual salen 7.428 contratos, 6 hallazgos R3, ninguno R4, 17.260 procesos y 4.147 adjudicados.
- «Alguna fila adjudicada» puede contar como adjudicado un portafolio donde un lote falló y otro se adjudicó. Es la lectura de R5 más cercana a su texto, y I3 hereda ese sesgo; se revisa al calcular I3.
- Las tareas siguientes agregan sus filas a `quality_issues`. Publicarla en `data/outputs/` (calidad de datos) es trabajo de `publish/`.

## Alternativas

- **Adjudicado por la fila más reciente:** descartada. Marcaría como no adjudicado a un portafolio que sí se adjudicó antes.
- **Máximo de oferentes solo entre las filas adjudicadas:** descartada. Cambiaría el texto de R5.
- **Una tabla de calidad por regla:** descartada. Publicar una sola salida de calidad exige una tabla única.
- **Resolver el valor final con MEData aquí:** descartada. Mezclaría la consolidación con el cruce (R7, R8).
