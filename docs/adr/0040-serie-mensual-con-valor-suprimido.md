# 0040. Serie mensual: el conteo siempre se publica y el valor se suprime con R13

- **Estado:** Aceptada
- **Fecha:** 2026-11-05
- **Fuente:** [docs/reglas.md](../reglas.md#4-reglas) (R7, R12, R13, D3, D4, D6) y sección 7 («Serie mensual»), [docs/producto.md](../producto.md) (pantallas 3 y 5)

## Contexto

La pantalla 3 dibuja la contratación directa por mes, y la 5 compara la prestación de servicios con el resto. Hace falta una salida con contratos y valor por mes, modalidad y tipo. R13 suprime los indicadores desagregados «por mes» con menos de 5 contratos, pero en los meses de restricción la contratación directa baja a 0–2 contratos (febrero a mayo de 2022): suprimir la celda entera esconde justo la caída que muestra el hallazgo.

## Decisión

- **Salida `monthly_series.json`** (`indicators/monthly_series.{py,sql}`, `publish/series.py`, modelo `MonthlySeries`): una fila por mes, modalidad y tipo del Distrito, con `contract_count`, `value_sample_size`, `value` e `is_suppressed`. Una modalidad o un tipo vacíos son el total de esa dimensión, así que el tablero no suma nada (el dominio vive en Python).
- **El conteo siempre se publica.** Es la `n` que R13 ya publica en toda celda suprimida; ocultarlo no protegería a nadie y borraría la caída de los meses de restricción.
- **El valor se suprime con R13.** Un valor respaldado por entre 1 y 4 contratos con valor (R7, D3) no se publica (D4). Con cero contratos con valor, el valor es cero y se publica: no hay nada que despejar.
- **Supresión complementaria (D6)** sobre el valor, hasta que ningún desglose cambie. Si un desglose queda con un solo valor suprimido, se suprime también el publicado de menor `value_sample_size` que tenga contratos. Los desgloses son los tipos de una modalidad y mes, las modalidades de un tipo y mes, las modalidades y los tipos de un mes, y los meses de un año (cuya suma coincide con la cifra anual que I1 ya publica).
- **Espejos.** Las filas del mismo mes con los mismos contratos con valor y el mismo valor (una hoja que es la única hija con contratos de un total publicado) se ocultan juntas: ocultar una sola no protege nada. Un verificador independiente encontró 35 valores de menos de 5 contratos que se despejaban en cascada sin esta regla, y `test_d6_series_published_suppression_cannot_be_undone_by_propagating_totals` propaga todos los desgloses sobre la salida publicada para que no vuelva a pasar.
- **Meses vacíos como cero.** La serie va del primer mes con firma al mes de la fecha de corte (R12), y cada combinación publicada trae todos los meses, para que el tablero no tenga que inferir ceros.
- **Conteo y valor como I1.** El conteo incluye todos los contratos firmados del mes (R7: el crédito público cuenta); el valor es el valor inicial (D3) de los que cuentan en los indicadores de valor.
- La supresión de la serie vive en `publish/series.py` y reutiliza `SUPPRESSION_THRESHOLD`. No toca `suppress_small_cells`, así que las celdas ya publicadas de I1, I2 e I8 no cambian.

## Consecuencias

- Con la copia (enero de 2022 a octubre de 2026, 58 meses): 2.088 filas, 757 con el valor suprimido. El conteo de los meses de restricción se ve completo.
- D6 oculta valores grandes cuando su complemento es pequeño. En enero de 2022 hay 723 contratos directos y solo 3 de régimen especial: la única parte publicada que despejaría el valor de esos 3 es la directa, así que su valor no se publica, aunque su conteo sí. La cifra anual de la contratación directa sigue en I1.
- El tablero debe mostrar «datos insuficientes» en el valor suprimido y dibujar el conteo.
- Los periodos de restricción para sombrear la pantalla 3 no salen de esta serie; quedan fuera de este ADR.

## Alternativas

- **Solo conteos, sin valor:** descartada. Es más simple, pero se aparta de la sección 7 («contratos y valor») y la pantalla 3 no podría mostrar el valor mensual.
- **Sin R13, como la conciliación (ADR 0038):** descartada. En celdas de un contrato de prestación de servicios publicaría el valor de un contrato con una persona natural, que es lo que R13 evita; la conciliación solo cuenta contratos.
- **Suprimir también el conteo bajo 5:** descartada. Esconde la caída de los meses de restricción, que es lo que la pantalla 3 debe mostrar.
