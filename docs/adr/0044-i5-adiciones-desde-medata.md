# 0044. I5 mide las adiciones solo con MEData y publica la variante cerca del tope del 50 %

- **Estado:** Aceptada
- **Fecha:** 2026-11-05
- **Fuente:** [docs/indicadores.md](../indicadores.md#1-catálogo) (I5), [docs/reglas.md](../reglas.md#4-reglas) (R7, R8, R13, D3), [ADR 0025](0025-normalizacion-de-adiciones.md), [ADR 0039](0039-i1-anual-por-secretaria.md)

## Contexto

I5 pregunta cuánto crecen los contratos después de firmados. La fórmula del catálogo cuenta contratos con adición y compara el valor adicionado con el valor inicial. Antes de implementarlo se contrastó SECOP II con MEData sobre la copia del 1 de noviembre, y salieron tres hechos:

- **El valor de SECOP II ya incluye las adiciones.** En los 419 contratos con adiciones en valor en MEData, el valor de la primera versión de SECOP II es igual al valor final de MEData en 378 y al inicial en 5. Cierra la pregunta abierta del 29 de octubre.
- **«Adicion en el valor» de SECOP II subcuenta.** De esos 419 contratos, solo 79 traen ese tipo en Adiciones; la mayoría figura como `Modificacion General`. El criterio del [ADR 0025](0025-normalizacion-de-adiciones.md) no se confirma, y 100 contratos con ese tipo tienen 0 adiciones en MEData.
- **El tope del 50 % se ve en los datos.** Adicionado ÷ valor inicial de MEData: menos de 10 %, 82 contratos; de 10 a 25 %, 103; de 25 a 40 %, 80; de 40 a 45 %, 16; de 45 a 50 %, 185; más de 50 %, 9.

## Decisión

- **Fuente.** Solo MEData: los contratos de `linked_contracts` que están en MEData, con `initial_value` y `total_addition_value` de MEData. Cubre contratos firmados del 4 de enero de 2022 al 30 de junio de 2023, así que se publican 2022 y 2023 (parcial).
- **Periodo y nivel.** Año de la fecha de firma. Distrito y cada secretaría de R8, incluida «sin asignar», para que sumen al Distrito (D6).
- **Contratos con adición.** Contratos con `total_addition_value > 0` ÷ contratos de MEData con monto informado. Un monto vacío no es «sin adición»: el contrato sale del denominador (29 contratos). `sample_size` es el denominador.
- **Valor adicionado.** Suma de `total_addition_value` ÷ suma de `initial_value` de MEData, sin crédito público (R7) ni contratos sin valor inicial. `sample_size` son los contratos con valor.
- **Cerca del tope (variante `near_addition_cap`).** Contratos cuya adición llega al 45 % del valor inicial ÷ contratos con adición, solo por número. Describe cuántos contratos con adición están cerca del límite legal del 50 %; no los califica. El umbral del 45 % es una decisión de presentación, no una regla legal: queda como constante del SQL.
- **Supresión.** R13 y D6 se aplican en `publish_indicators` sin cambios.
- **SECOP II Adiciones no entra a I5.** Sirve para ocurrencia y fecha de las modificaciones, no para contar adiciones en valor.

## Consecuencias

- `indicators.json` agrega las celdas de I5 (1.898 líneas, solo adiciones). El contrato no cambia: `IndicatorCell` ya admite `I5`.
- Con la copia actual: 353 de 1.522 contratos de 2022 (23,2 %) y 66 de 1.081 de 2023 (6,1 %) tienen adición. La diferencia entre años refleja el seguimiento: MEData se detuvo en diciembre de 2023, así que los contratos de 2023 tuvieron menos tiempo de acumular adiciones registradas. El tablero lo aclara.
- I5 no cubre 2024–2026. Es una limitación de la fuente y se muestra como tal.
- **Queda abierto:** como el valor de SECOP II incluye las adiciones, la frase de D3 y de `indicadores.md` §3 («valor inicial = primera versión firmada, sin adiciones») no se cumple para los contratos con adiciones. Las proporciones por valor de I1 e I2 casi no se mueven (menos de 1 punto en 2022 y 2023), pero el texto se corrige en una tarea aparte.

## Alternativas

- **Contar con «Adicion en el valor» de SECOP II para 2022–2026:** descartada. Subcuenta unas cuatro de cada cinco adiciones reales y daría una proporción baja que parecería un hallazgo.
- **MEData como cifra base y SECOP II como variante:** descartada. Añade celdas y explicaciones para una cifra que se sabe incompleta.
- **Umbral del 50 % para la variante:** descartada. El 50 % es un máximo legal y 185 contratos están entre el 45 y el 50 %; un umbral en el tope dejaría fuera casi todos los que se acercan.
