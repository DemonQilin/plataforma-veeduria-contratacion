# 0033. La celda de indicador en el contrato

- **Estado:** Aceptada
- **Fecha:** 2026-11-04
- **Fuente:** [docs/reglas.md](../reglas.md#4-reglas) (R13, R16), [ADR 0004](0004-contrato-pydantic-json-schema-ts.md), [ADR 0005](0005-dominio-solo-en-python.md), [ADR 0032](0032-run-from-snapshot-publica-con-escritura-atomica.md)

## Contexto

El contrato solo tenía `Metadata`. La supresión de celdas pequeñas (R13), el cálculo de I2 e I8 y la prueba de privacidad necesitan una forma común para una cifra de indicador. Sin ella, cada indicador inventaría la suya y la supresión no se podría probar de una vez.

## Decisión

- **`IndicatorCell`** (`publish/models.py`): un indicador, en un nivel y un periodo. Campos: `indicator` (I1–I8), `variant`, `measure` (`count` o `value`), `level` (`district` o `department`), `department`, `period` (`AAAA` o `AAAA-MM`), `sample_size`, `numerator`, `denominator`, `ratio` e `is_suppressed`.
- **`Indicators`** envuelve la lista de celdas y se registra en `CONTRACT_MODELS`, así que su esquema sale en `data/schema/indicators.json`.
- **El modelo hace imposible una celda incoherente.** Una celda suprimida no puede traer numerador, denominador ni razón. Una celda publicada trae las tres cifras (R16). La secretaría va si y solo si el nivel es `department`.
- **La celda suprimida publica su `sample_size`.** Un conteo de contratos no identifica a nadie por sí solo y da contexto al lector (`docs/producto.md`: «cada cifra muestra su n»).
- **`sample_size` siempre cuenta contratos**, también cuando la medida es de valor, porque R13 se define sobre contratos.
- **`ratio` y no `value`:** «valor» ya significa dinero en el glosario (`initial_value`, `is_value_eligible`).

## Consecuencias

- Este ADR solo define la forma. Qué celdas se suprimen, incluida la supresión complementaria, lo decide `publish/` en la tarea siguiente.
- `indicators.json` todavía no se escribe: se agrega a `write_outputs` y a `web/src/lib/data.ts` cuando existan I2 e I8.
- Cambiar un campo de la celda es cambiar el contrato: hay que regenerar el esquema y los tipos en el mismo commit.
