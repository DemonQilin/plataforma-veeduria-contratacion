# 0027. Normalización de proveedores: NIT sin dígito de verificación y un nombre por NIT

- **Estado:** Aceptada
- **Fecha:** 2026-11-03
- **Fuente:** [docs/reglas.md](../reglas.md#4-reglas) (R14), [docs/indicadores.md](../indicadores.md) (I4)

## Contexto

I4 suma el valor adjudicado por proveedor, así que necesita una llave estable. La copia de proveedores (4.459 filas de 4.459 contratos) tiene 975 documentos distintos y dos problemas:

- 24 documentos tienen 10 dígitos. En 23 el último dígito coincide con el dígito de verificación de la DIAN calculado sobre los 9 primeros. Tres de ellos también aparecen con 9 dígitos, así que el mismo proveedor contaría dos veces.
- 11 NIT tienen más de un nombre (sigla y razón social, con o sin punto final), por ejemplo uno con 105 filas.

## Decisión

- **`supplier_id` es el NIT sin dígito de verificación.** Un documento de 10 dígitos pierde el último solo si coincide con el calculado con los pesos de la DIAN; si no coincide queda con 10 dígitos y va al reporte de calidad (hoy es 1 documento).
- **`supplier_name` es el nombre más frecuente del NIT**, recortado; en un empate gana el primero en orden alfabético. Una sola salida por NIT mantiene I4 determinista (regla 3).
- **Un nombre vacío no cuenta**: un NIT solo queda sin nombre si ninguna de sus filas lo trae.
- **Una fila por fila de la copia**, sin deduplicar y sin filtro de fecha, igual que en Contratos, Procesos y Adiciones (ADR 0023, 0024, 0025). El filtro de privacidad es el del [ADR 0026](0026-proveedores-nit-de-9-o-10-digitos.md).
- Los nombres y los NIT distintos se calculan en Python y llegan al SQL como listas paralelas (ADR 0021, 0022).

## Consecuencias

- `suppliers` queda con 3 columnas: `contract_id`, `supplier_id`, `supplier_name`.
- La prueba golden fija 4.459 filas, 4.459 contratos, 972 `supplier_id`, 1 con 10 dígitos y ninguno sin nombre.
- Dos NIT distintos de un mismo grupo empresarial siguen siendo dos proveedores; unirlos exigiría una fuente que no tenemos.
- El nombre más frecuente puede no ser la razón social completa. Se publica tal como viene en la fuente.

## Alternativas

- **Llave por nombre:** descartada. Un NIT tiene hasta dos nombres y un nombre puede variar por un punto.
- **Dejar el dígito de verificación:** descartada. Dividiría la concentración de 3 proveedores en I4.
- **Quitar siempre el último dígito de 10:** descartada. Hay 1 documento cuyo último dígito no coincide, y quitarlo sin verificar inventaría un NIT.
