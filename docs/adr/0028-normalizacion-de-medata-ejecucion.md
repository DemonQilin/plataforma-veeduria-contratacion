# 0028. Normalización de MEData · Ejecución: una fila por línea y reparación sobre textos distintos

- **Estado:** Aceptada
- **Fecha:** 2026-11-03
- **Fuente:** [docs/reglas.md](../reglas.md#4-reglas) (R2, R6), [ADR 0010](0010-parser-medata-y-ftfy.md)

## Contexto

La copia de MEData · Ejecución tiene 25.783 líneas presupuestales de 2.939 contratos. Trae las tildes rotas, los montos con puntos de miles y coma decimal (`54.600.000,00`), las fechas como `d/mm/yyyy` y el año como `2022.0`. 2.072 líneas están cortadas en origen y llevan `truncated`, sin valores, duración, estado ni año.

## Decisión

- **Una fila por línea de la copia**, sin colapsar a contrato, igual que Procesos (ADR 0024). Colapsar y cruzar con SECOP II (R7, R8) es un paso posterior.
- **`fecha_contrato` es la fecha de firma (`signed_date`).** Se lee con `%d/%m/%Y`; una fecha ilegible queda nula.
- **R2 como en Contratos:** se quitan las filas con firma anterior al 1 de enero de 2022 y se conservan las de fecha nula. Con la copia actual no sale ninguna.
- **La codificación se repara con `ftfy.fix_encoding` en Python**, sobre los textos distintos de `modalidad`, `causal`, `nombre_secretaria`, `nombre_programa` y `estado`, antes de clasificar la modalidad (ADR 0010). El resultado llega a DuckDB como listas paralelas (ADR 0021, 0022, 0027).
- **Las filas truncadas se conservan** con `truncated = true` y los valores, la duración, el estado y el año nulos. Sirven para conteos, fechas, modalidad y secretaría.
- **`contrato` pasa a `contract_reference`**, la llave contra `referencia_del_contrato` de SECOP II.

## Consecuencias

- `contract_execution` tiene 15 columnas y 25.783 filas; la prueba golden fija 2.939 referencias, 2.072 truncadas, ninguna modalidad `other` y ningún texto con `Ã`.
- Quien consuma la tabla debe tratar los valores nulos de las filas truncadas como desconocidos, no como cero.
- Un contrato puede tener más de una modalidad entre sus líneas (hoy 1). La tarea de colapso debe decidir cuál gana.

## Alternativas

- **Reparar toda la tabla con una función de DuckDB definida desde Python:** descartada. El SQL dejaría de ser autónomo y se acoplaría al conector.
- **Descartar las filas truncadas:** descartada. Perdería 8 % de las líneas que sí tienen fecha, modalidad y secretaría.
- **Colapsar a contrato aquí:** descartada. Mezclaría la limpieza con la regla de asignación de R8.
