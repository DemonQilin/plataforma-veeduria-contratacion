# 0046. La referencia del contrato se normaliza sin espacios en los extremos

- **Estado:** Aceptada
- **Fecha:** 2026-11-05
- **Fuente:** [docs/reglas.md](../reglas.md#4-reglas) (R3, R8, R15), [docs/fuentes.md](../fuentes.md) sección 7, [docs/indicadores.md](../indicadores.md) (I5), [ADR 0030](0030-cruce-y-catalogo-de-secretarias.md), [ADR 0031](0031-conciliacion-secop-medata.md), [ADR 0044](0044-i5-adiciones-desde-medata.md)

## Contexto

SECOP II y MEData se cruzan por igualdad exacta de la referencia del contrato (`referencia_del_contrato` y `contrato`). La revisión C4 vio una diferencia en I5 y propuso, sin verificarla, que el cruce reconocía más formatos. Al rehacer el cálculo desde los CSV de la copia pasó lo contrario:

- Un recálculo independiente, con la referencia en mayúsculas y sin espacios en ambos lados, coincide con el pipeline en 2022 (1.524 contratos, 353 con adición) y da un contrato más en 2023 (1.080 frente a 1.079).
- Ese contrato es el `4600098086`, firmado el 16 de mayo de 2023. SECOP II lo guarda con un espacio no separable (U+00A0) al final, así que no igualaba al de MEData y quedaba con `in_medata = false`.
- La conciliación R15 y I5 usan el mismo cruce, y ambos lo perdían.
- Las cifras de C4 (1.510 y 1.072 contratos) no se reprodujeron con el mismo método. El pipeline no normalizaba ninguna referencia.

## Decisión

- **`trim()` en las dos normalizaciones.** `normalize/r06_contracts.sql` y `normalize/r02_contract_execution.sql` guardan `contract_reference` sin espacios ni espacios no separables en los extremos. DuckDB `trim()` quita ambos. Los cruces siguen por igualdad exacta, ahora sobre referencias limpias.
- **Solo los extremos.** No se cambian mayúsculas ni el interior de la referencia.
- **Sin colisiones.** Antes y después de recortar hay 7.428 referencias distintas en SECOP II y 2.939 en MEData, así que R3 no consolida filas que antes eran distintas. Solo 2 filas de SECOP II tienen espacios en los extremos.
- Una prueba por normalización y una de la copia fijan el caso del `4600098086`.

## Consecuencias

- Contratos que cruzan con MEData: 2.633, antes 2.632. Los de ambas fuentes en la conciliación suman 2.629, antes 2.628. La cobertura de MEData en SECOP II sigue en 90 % y quedan 306 sin cruce, antes 307.
- I5 2023 en el Distrito: 1.080 contratos con monto informado, antes 1.079, y 1.078 con valor, antes 1.077. Los 66 con adición no cambian. Una secretaría cambia su celda y R15 cambia un mes. Ningún valor cruza el umbral del 80 % ni el de supresión.
- El diferencial de 21 contratos de C4 queda explicado: 1 es este defecto y los demás eran del recálculo de C4.

## Alternativas

- **Normalizar también el formato «NNNNNNNNNN de 2022»:** descartada por ahora. Hay 230 referencias de SECOP II con ese formato, y MEData trae solo el número. Puede explicar parte de los contratos de MEData sin cruce, pero no está verificado y cambia la llave del cruce. Queda como pregunta abierta en la bitácora.
- **Recortar solo en el cruce:** descartada. Dejaría la referencia sucia en `canonical_contracts` y en cada tabla que la use.
