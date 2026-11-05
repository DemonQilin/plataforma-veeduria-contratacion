# 0042. `quality.json` publica la calidad de datos completa (R4, R6, R8)

- **Estado:** Aceptada
- **Fecha:** 2026-11-05
- **Fuente:** [docs/reglas.md](../reglas.md#4-reglas) (R4, R6, R8, R13), [ADR 0010](0010-parser-medata-y-ftfy.md), [ADR 0028](0028-normalizacion-de-medata-ejecucion.md), [ADR 0030](0030-cruce-y-catalogo-de-secretarias.md), [ADR 0038](0038-r15-publicada-sin-supresion.md)

## Contexto

`quality.json` solo publicaba la conciliación R15 (ADR 0038). La sección 7 de `docs/reglas.md` pide también el porcentaje sin secretaría, las filas truncadas de MEData y los valores no reconocidos en los catálogos, y R4 exige que cada exclusión se reporte. Los datos existen en el pipeline (`quality_issues`, `linked_contracts`, `medata_contracts`), pero nada los publicaba, y los textos crudos que los catálogos no reconocen no quedaban en ninguna tabla.

## Decisión

- **Sin secretaría (R8).** Conteo, total y proporción de los contratos con `department_source = 'unassigned'`, para el Distrito y por año de firma.
- **Filas truncadas de MEData (ADR 0010, ADR 0028).** Dos medidas: las líneas de MEData · Ejecución cortadas en origen y los contratos de MEData cuyas líneas vienen todas cortadas (los que no tienen valor).
- **Registros sin firma (R4).** Conteo y proporción de los registros excluidos sobre el total de registros de SECOP II. No se desagrega por año, porque no tienen fecha de firma.
- **Valores no reconocidos (R6).** Una fila por catálogo, fuente y texto crudo, con el número de filas de la copia que lo traen. Un texto es no reconocido cuando su clave de comparación no está en el catálogo; no sirve contar el código `other`, porque los catálogos listan a propósito textos conocidos bajo «Otro» (`docs/reglas.md`, sección 3). Los textos son etiquetas de columnas de la lista blanca (modalidad, tipo de contrato, tipo de proveedor, tipo de adición, secretaría), no datos de personas.
- **R13 no se aplica**, por la misma razón que en ADR 0038: son conteos agregados del Distrito y etiquetas de catálogo. Nunca se publica una referencia ni un identificador de contrato; una prueba lo verifica.
- **Fuera de este ADR:** la exclusión de R9 (proceso con cero oferentes) la publica el indicador I3, que extiende este mismo modelo.

## Consecuencias

- `quality.json` agrega `unassigned_share`, `truncated_rows`, `unsigned_records` y `unrecognized_values` junto a `reconciliation`.
- Los textos no reconocidos se detectan en la normalización y se anotan en `quality_issues` con la regla `R6`; `build_quality` solo lee tablas, como hasta ahora.
- Si un catálogo empieza a traer un texto con datos de personas, esta decisión se revisa; no se oculta el valor en silencio.

## Alternativas

- **Publicar solo el conteo de valores no reconocidos, sin el texto:** descartada. No permite revisar el catálogo, que es el fin del reporte.
- **Suprimir con R13 las proporciones por año:** descartada por la misma razón que ADR 0038; no describe personas.
