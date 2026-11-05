# 0034. Calendario electoral y ventanas de comparación

- **Estado:** Aceptada
- **Fecha:** 2026-11-04
- **Fuente:** [docs/reglas.md](../reglas.md#4-reglas) (R10, R11, R12), [docs/indicadores.md](../indicadores.md) sección 3, [docs/fuentes.md](../fuentes.md) sección 10

## Contexto

I2 compara la contratación directa de enero en los años de restricción con la de los años de control. Las ventanas dependen de las fechas de la Ley de Garantías, que no se pueden inferir de los datos (R10). Además, `indicadores.md` decía que el denominador va «de enero a octubre», pero la fecha de corte de la copia es el 30 de octubre de 2026 (R12): a 2026 le falta el 31.

## Decisión

- **El calendario es `pipeline/reference/electoral_calendar.toml`.** Una tabla `[[restriction]]` por restricción, con `cycle`, `scope`, `start`, `end` y `sources`. Las fechas son fechas nativas de TOML. Una restricción sin fuente, con el inicio después del fin, con un alcance desconocido o con un ciclo repetido es un error del catálogo (`CatalogError`).
- **`scope` distingue qué contratación se limita:** `direct_award` (restricción presidencial) o `interadministrative` (territorial). Solo `direct_award` genera ventanas de I2.
- **Ventanas de tratamiento:** del 1 de enero al día anterior al inicio de la restricción (2022: 28 ene; 2026: 30 ene).
- **Ventanas de control:** los años intermedios sin restricción directa usan el punto medio de las ventanas de tratamiento (29 ene). Si el punto medio no fuera un día entero, el cálculo falla en lugar de redondear.
- **Denominador (R12):** del 1 de enero al día y mes de la fecha de corte, en todos los años (tramo común). Hoy es el 30 de octubre. Si el corte es un 29 de febrero, los años no bisiestos usan el 28.
- **Las locales de 2023 y 2027 no están en el calendario** hasta que sus fechas se verifiquen con fuente oficial. I2 no las usa.
- El fin de la restricción presidencial (19 jun 2022, 21 jun 2026) queda en la ventana de tratamiento para el factor de confusión 3.

## Consecuencias

- Cambiar una fecha es editar el TOML y su fuente; las ventanas se recalculan solas.
- «De enero a octubre» deja de ser una constante: si la copia se actualiza con un corte distinto, el denominador de todos los años se mueve con él.
- Cuando se verifiquen las locales de 2023, se agregan al TOML sin tocar el código.
