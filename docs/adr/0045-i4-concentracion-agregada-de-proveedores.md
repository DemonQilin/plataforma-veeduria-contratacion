# 0045. I4 mide la concentración de proveedores solo de forma agregada

- **Estado:** Aceptada
- **Fecha:** 2026-11-05
- **Fuente:** [docs/indicadores.md](../indicadores.md#1-catálogo) (I4), [docs/reglas.md](../reglas.md#4-reglas) (R7, R8, R13, R14, D3, D6), [docs/plan.md](../plan.md) (planes B), [ADR 0027](0027-normalizacion-de-proveedores.md), [ADR 0039](0039-i1-anual-por-secretaria.md)

## Contexto

I4 pregunta si unas pocas empresas reciben buena parte del dinero. El catálogo lo define como el valor de las 5 personas jurídicas con más valor ÷ el valor total a personas jurídicas, y planeaba publicar sus nombres (R14). Tres hechos condicionan la decisión:

- **Los organizadores no han respondido.** El correo con la pregunta sobre nombrar personas jurídicas se envió el 5 de noviembre y pide respuesta antes del 7. El plan B del [plan](../plan.md) (sección 7) dice que, sin permiso, I4 se reporta solo agregado.
- **`IndicatorCell` no tiene dónde poner nombres.** Publicarlos exigiría una salida y un modelo nuevos, y el congelamiento es el 8 de noviembre.
- **Con 5 proveedores o menos, la razón es 100 % por construcción.** Una secretaría con cinco proveedores o menos no dice nada sobre concentración.

## Decisión

- **Solo agregado, sin nombres.** I4 publica cifras en `indicators.json` y ningún `supplier_id` ni `supplier_name` sale del cálculo. Una prueba lo fija. Si los organizadores autorizan nombrar personas jurídicas, la salida con nombres es una decisión aparte.
- **Fórmula.** Valor inicial (D3) de los 5 proveedores con más valor ÷ valor total a personas jurídicas, por año de la fecha de firma de SECOP II, en el Distrito y en cada secretaría de R8, incluida «sin asignar», para que sumen al Distrito (D6). Solo por valor: `measure = "value"`, sin variantes. El año de la fecha de corte queda parcial, como en I1.
- **Universo.** Contratos de `linked_contracts` con fila en `suppliers` (solo personas jurídicas con NIT, R14), sin crédito público ni contratos sin valor (R7). `sample_size` es el número de contratos de la celda, la `n` de R13.
- **Cruce proveedor ↔ contrato por referencia.** `suppliers.contract_id` apunta a cualquier versión del contrato, no solo a la canónica; con la copia actual, 24 filas de proveedores pertenecen a otra versión. Se cruza `suppliers → contracts → linked_contracts` por `contract_reference`. Si una referencia tuviera proveedores distintos en sus versiones, gana el de la versión canónica y luego el NIT menor, para que cada contrato cuente una vez y la salida sea determinista.
- **Empates.** El orden es valor descendente y NIT; un empate en el quinto puesto no cambia la suma.
- **Supresión.** R13 y D6 se aplican en `publish_indicators`. Además, una secretaría con `TOP_SUPPLIERS` (5) proveedores distintos o menos se publica ya suprimida: conserva `sample_size` y oculta numerador, denominador y razón. D6 la trata como cualquier celda suprimida. El Distrito siempre se publica. Con la copia actual salen suprimidas 31 de 132 celdas de secretaría.
- **Sin cambio de contrato.** `IndicatorCell` ya admite `I4`; `data/schema/` y los tipos de TypeScript no cambian.

## Consecuencias

- Cifras del Distrito: 43,1 % (2022), 50,9 % (2023), 35,6 % (2024), 49,8 % (2025) y 30,9 % (2026, parcial). En 2022 son 915 contratos y 1,109 billones de 2,571 billones de pesos.
- Cobertura: 48 contratos con proveedor persona jurídica no tienen fila en `suppliers` (4.483 frente a 4.435) y quedan fuera. Por la regla de privacidad (ADR 0017, ADR 0026) `suppliers` descarta los NIT que parecen cédulas; si una empresa real tiene un NIT de 8 dígitos, no cuenta.
- El tablero no puede decir qué empresas concentran el valor. Es una limitación consciente, no un hallazgo.
- Un valor alto marca un patrón para revisar, no una irregularidad: hay objetos que solo una empresa grande puede cumplir.

## Alternativas

- **Esperar la respuesta para publicar nombres:** descartada. No hay respuesta, el tiempo corre y publicar nombres sin permiso contradice R14.
- **Publicar las secretarías de 5 proveedores o menos con razón 1,0:** descartada. Es un tope aritmético que parece una señal, y la celda no trae el número de proveedores para explicarlo.
- **Cruzar solo por el `contract_id` canónico:** descartada. Pierde 24 contratos cuyo proveedor figura en otra versión.
- **Medir también por número de contratos:** descartada. Con 972 proveedores y una cola larga de contratos pequeños, el valor es lo que dice el catálogo y evita una segunda cifra que explicar.
