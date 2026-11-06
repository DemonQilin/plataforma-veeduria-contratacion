# 0047. La referencia de SECOP II se reduce al número cuando trae «de AAAA» o un signo final

- **Estado:** Aceptada
- **Fecha:** 2026-11-05
- **Fuente:** [docs/reglas.md](../reglas.md#4-reglas) (R3, R8, R15), [docs/fuentes.md](../fuentes.md) sección 5, [docs/indicadores.md](../indicadores.md) (I5), [ADR 0046](0046-referencia-sin-espacios-en-los-extremos.md), [ADR 0044](0044-i5-adiciones-desde-medata.md)

## Contexto

El ADR 0046 dejó abierta una alternativa: SECOP II guarda 430 referencias que no son solo dígitos, y MEData guarda solo el número. Se midió sobre la copia: los pares, las secretarías y los valores con las tablas del pipeline en memoria, y las cifras de cierre con un recálculo independiente desde los CSV.

- Hay 200 contratos de MEData sin cruce cuyo número coincide con el comienzo de una referencia de SECOP II. Son 132 con «de», 65 con «DE», 1 con «-AAAA», 1 con un punto final y 1 con un asterisco final.
- Los 200 pares tienen la misma secretaría (según el catálogo) y el mismo año de firma. La diferencia en días entre las dos fechas de firma se parece a la de los 2.633 pares que ya cruzaban: SECOP II firma, en general, entre 0 y 8 días después.
- Los valores difieren más de un 1 % en 16 de 193 pares con valor (8 %); entre los 2.633 pares exactos, en 427 de 2.604 (16 %).
- Ningún número inicial corresponde a dos procesos de contratación distintos.
- Ocho números aparecen en SECOP II dos veces, una limpia y otra con sufijo o signo, siempre en el mismo proceso: `4600094321`, `4600096861`, `4600097281`, `4600099328`, `4600105052`, `4600105960`, `4600106046` y `4600107099`. Hoy R3 los cuenta como contratos distintos.
- Una referencia que el patrón reduce lleva un año distinto del de firma (`4600093090 de 2021`, firmada en 2022). El número sigue identificando el contrato, así que no se usa el año para decidir.

## Decisión

- **Un patrón, en la normalización de SECOP II.** `normalize/r06_contracts.sql` recorta la referencia (ADR 0046) y, si el texto entero coincide con `^([0-9]+)(?:\s*(?:del?|-)\s*[0-9]{4})?\s*[.*-]?$` sin distinguir mayúsculas, guarda solo los dígitos. Si no coincide, la deja como estaba.
- **`contract_reference` sigue siendo la llave.** R3, R8, R15 e I4 leen el mismo valor, y los cruces siguen por igualdad exacta. No cambia la normalización de MEData: sus referencias ya son solo dígitos.
- **Lo que no se toca:** `CO1.PCCNTR.N`, `CM N`, `CONVENIO N° N DE N`, `N DE N (DISTRITO) Y CT-N-N (EPM)`, años de dos o cinco dígitos y cualquier otro texto.
- El patrón exige que el texto entero coincida: `N DE N (DISTRITO) Y CT-N-N (EPM)`, que lleva otro número de contrato, queda como está.

## Consecuencias

Con la copia, verificado con un recálculo independiente desde los CSV:

- **Contratos canónicos:** 7.420, antes 7.428. Las 8 fusiones de R3 dejan `version_count = 2` en esos contratos. 418 referencias cambian de texto.
- **Cruce con MEData:** 2.833 contratos, antes 2.633; quedan 106 sin cruce, antes 306. La fuente de la secretaría pasa a MEData en 2.833, SECOP II en 4.568 y sin asignar en 19 (antes 2.633, 4.776 y 19).
- **R15:** los contratos en ambas fuentes dentro de los 18 meses suman 2.829, antes 2.629. **Junio y julio de 2022 dejan de estar por debajo del 80 %** (88,7 % y 86,1 %); quedan marzo, abril, mayo y diciembre de 2022. Enero de 2022 pasa de 661 de 790 a 722 de 729. La regla y el umbral no cambian.
- **I5:** 387 de 1.632 contratos de 2022 con adición (antes 353 de 1.524) y 69 de 1.165 de 2023 (antes 66 de 1.080). Tope: 164 de 387 y 25 de 69. La secretaría `general` gana dos celdas de conteo cerca del tope (2022 y 2023), que pasan por la supresión R13 como las demás.
- **I1, I2, I4 e I8:** bajan 1 contrato en 2022, 3 en 2023, 3 en 2025 y 1 en 2026, que son las fusiones de R3. Por ejemplo, el denominador de I1 por valor de 2022 baja 199.999.254, el valor de `4600094321`. I3 no cambia.
- **Ninguna cifra publicada queda con menos de 5 contratos** ni cruza el umbral de supresión.
- La cifra titular (I2 por número, 58 % y 65 %) no se mueve al redondear.

## Alternativas

- **Solo «de AAAA», sin los signos finales:** descartada. Perdería 3 de los 200 cruces y dejaría sin fusionar 6 de las 8 duplicaciones de R3, que son el mismo contrato escrito con un punto o un guion.
- **Cruzar por el número al unir, sin cambiar la referencia:** descartada por la misma razón que en el ADR 0046. Dejaría la referencia sucia en `canonical_contracts`, y R3 seguiría contando dos veces los 8 contratos.
- **Usar el año del sufijo para validar el cruce:** descartada. Una referencia trae un año distinto del de firma, y el año de firma de MEData ya coincide en los 200 pares.
