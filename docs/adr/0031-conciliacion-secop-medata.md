# 0031. Conciliación mensual SECOP–MEData

- **Estado:** Aceptada
- **Fecha:** 2026-11-04
- **Fuente:** [docs/reglas.md](../reglas.md#4-reglas) (R15), [ADR 0030](0030-cruce-y-catalogo-de-secretarias.md)

## Contexto

R15 pide, por mes del periodo común, qué proporción de contratos aparece en ambas fuentes, y advertir si baja del 80 %. Con la copia, los contratos compartidos no firman siempre el mismo mes: en 2.503 de los 2.632 la fecha de MEData es posterior a la de SECOP II (mediana de 5 días, percentil 90 de 14), y 412 caen en otro mes.

## Decisión

- **Tabla `reconciliation`** (`link/r15_reconciliation.sql`, `link/reconciliation.py`): una fila por mes, desde el primer hasta el último mes de MEData, con `secop_count`, `medata_count`, `shared_count`, `union_count`, `shared_share`, `secop_coverage`, `medata_coverage` y `below_threshold`.
- **Mes:** el de la fecha de firma de SECOP II, que es la canónica (R3); la de MEData solo cuando el contrato no está en SECOP II. Así un contrato compartido cuenta una sola vez, en un solo mes.
- **Denominador:** la unión de las dos fuentes, como dice R15. Se guardan además la cobertura de SECOP II en MEData y la de MEData en SECOP II, porque responden preguntas distintas.
- **Umbral:** 80 % en `RECONCILIATION_THRESHOLD`. Se compara con conteos, no con el porcentaje redondeado, así que 4 de 5 no se advierte. Un mes sin contratos no se advierte y no tiene porcentaje.

## Evidencia (copia del 4 nov)

| Mes | SECOP II | MEData | Ambas | Unión | Ambas ÷ unión | Advertencia |
|---|---:|---:|---:|---:|---:|---|
| 2022-01 | 726 | 725 | 661 | 790 | 83,7 % |  |
| 2022-02 | 5 | 6 | 5 | 6 | 83,3 % |  |
| 2022-03 | 11 | 14 | 5 | 20 | 25,0 % | sí |
| 2022-04 | 14 | 18 | 13 | 19 | 68,4 % | sí |
| 2022-05 | 36 | 46 | 34 | 48 | 70,8 % | sí |
| 2022-06 | 60 | 62 | 52 | 70 | 74,3 % | sí |
| 2022-07 | 156 | 149 | 123 | 182 | 67,6 % | sí |
| 2022-08 | 199 | 198 | 181 | 216 | 83,8 % |  |
| 2022-09 | 191 | 188 | 180 | 199 | 90,5 % |  |
| 2022-10 | 114 | 118 | 108 | 124 | 87,1 % |  |
| 2022-11 | 147 | 156 | 140 | 163 | 85,9 % |  |
| 2022-12 | 57 | 48 | 40 | 65 | 61,5 % | sí |
| 2023-01 | 378 | 393 | 352 | 419 | 84,0 % |  |
| 2023-02 | 199 | 183 | 170 | 212 | 80,2 % |  |
| 2023-03 | 143 | 142 | 127 | 158 | 80,4 % |  |
| 2023-04 | 115 | 121 | 109 | 127 | 85,8 % |  |
| 2023-05 | 132 | 142 | 123 | 151 | 81,5 % |  |
| 2023-06 | 235 | 226 | 205 | 256 | 80,1 % |  |

- Seis de 18 meses quedan bajo el 80 %. Con la cobertura de SECOP II como medida serían tres (marzo, julio y diciembre de 2022).
- Cuatro contratos compartidos firmados en julio de 2023 según SECOP II (MEData los fecha en junio) quedan fuera de los 18 meses.
- Enero de 2022: 726 contratos en SECOP II y 725 en MEData por la fecha de SECOP II. Por la fecha propia de MEData son 727, la cifra de la primera validación; la diferencia son 2 contratos que SECOP II firma en febrero.

## Consecuencias

- La salida de calidad (`docs/reglas.md`, sección 7) toma esta tabla; la publicación llega con el cableado de `run`.
- Los meses de marzo a julio de 2022 tienen pocos contratos (11 a 156 en SECOP II), así que un contrato de diferencia mueve mucho el porcentaje. El tablero debe mostrar el conteo junto a la advertencia.
- La conciliación de `valor_total_adic_contrato` con `is_value_addition` (ADR 0025) sigue pendiente; no hace parte de R15.

## Alternativas

- **Solo SECOP II en MEData como denominador:** descartada. No es lo que dice R15 y oculta los contratos que solo están en MEData.
- **Mes de MEData:** descartada. Un contrato compartido caería en dos meses según la fuente.
