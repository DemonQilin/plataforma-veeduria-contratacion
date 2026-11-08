# 0036. Variante de I2 sin contratos interadministrativos

- **Estado:** Aceptada
- **Fecha:** 2026-11-05
- **Fuente:** [docs/indicadores.md](../indicadores.md) sección 3, [ADR 0034](0034-calendario-electoral-y-ventanas.md)

## Contexto

La concentración pre-restricción de I2 es sensible a los contratos interadministrativos. La restricción local de 2023 les quita los de julio a octubre del denominador de ese año, y en enero de 2022 no hay ninguno (causa no verificada). Medido el 4 de noviembre de 2026:

- Por número de contratos, la brecha entre tratamiento y control es de 37 puntos con ellos y de 43 sin ellos. Son diferencias de medias (promedio de 2022 y 2026 menos promedio de 2023 a 2025), no la métrica del criterio 1 de decisión, que compara el menor año de tratamiento con el valor más alto de control: 27,6 puntos con ellos y 30,5 sin ellos.
- Por valor, 2022 (30,7 %) casi no se distingue del control 2023 (28,9 %) si se incluyen.
- La variante `non_service_contract` ya está dominada por ellos: 1.436 de 1.708 directos que no son prestación de servicios de 2022 a 2026 (84 %), contando todas las fechas. En el tramo común (hasta el 30 de octubre de cada año) son 1.336 de 1.595 (84 %).

## Decisión

- I2 gana la variante `excluding_interadministrative`: la misma proporción con `contract_type <> 'interadministrative'` en el numerador y en el denominador, por número y por valor.
- **La definición base de I2 no cambia.** Las dos lecturas se publican sin elegir la definición después de ver los resultados.
- Redefinir I2 sin interadministrativos como cifra titular se deja para el punto de decisión 1 (T8), con ambas lecturas a la vista.

## Consecuencias

- `variant` es una cadena abierta en el contrato: no cambian `data/schema/` ni `web/src/types/contract.ts`.
- Un año sin contratos distintos de los interadministrativos no publica celda de esta variante.
- El glosario gana `excluding_interadministrative`.
