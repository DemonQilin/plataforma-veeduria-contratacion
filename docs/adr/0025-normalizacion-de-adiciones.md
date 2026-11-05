# 0025. Normalización de Adiciones: catálogo de tipos y solo «Adicion en el valor» cuenta para I5

- **Estado:** Aceptada
- **Fecha:** 2026-11-03
- **Fuente:** [docs/reglas.md](../reglas.md#4-reglas) (R1, R6), [docs/indicadores.md](../indicadores.md) (I5)

## Contexto

La copia de Adiciones de SECOP II tiene 15.884 filas de 5.990 contratos, y la mayoría no son adiciones de valor: `Modificacion General` 7.958, `No definido` 4.354, `Conclusion` 2.379, `Adicion en el valor` 642, `Reactivación` 262, `Suspensión` 244 y `Cesion` 45. I5 no puede contar filas como adiciones sin separar el `tipo` (`docs/bitacora.md`).

## Decisión

- **Catálogo de tipos** en `pipeline/reference/addition_types.toml` (R6): cada texto crudo pasa a un código (`value_addition`, `general_modification`, `closure`, `reactivation`, `suspension`, `assignment`, `undefined`). Lo que no esté en el catálogo cae en `other` y va al reporte de calidad.
- **Solo `value_addition` cuenta para I5.** *(Reemplazado por el [ADR 0044](0044-i5-adiciones-desde-medata.md): I5 usa MEData, porque este criterio subcuenta.)* La marca `is_value_addition` es verdadera únicamente para ese código (642 filas). Es un criterio provisorio: `Modificacion General` mezcla cambios de plazo, alcance o forma que no tienen monto, y contarla inflaría I5. La conciliación con `valor_total_adic_contrato` de MEData (R15, tarea 9) lo confirma o lo corrige.
- **R1 no se aplica aquí.** Adiciones no trae la entidad; la extracción pide solo los `id_contrato` de Contratos (ADR 0016) y no hay ids huérfanos. El cruce con `contracts` (tareas 7 y 8) lo garantiza.
- **Una fila por fila de la copia, sin deduplicar** y sin filtro de fecha, igual que en Contratos y Procesos (ADR 0023, ADR 0024). Ninguna combinación `id_contrato`, `tipo`, `fecharegistro` se repite.
- **Tipos:** `fecharegistro` pasa a `TIMESTAMP`; lo que no se pueda leer queda en `NULL`.
- El catálogo se aplica en Python sobre los textos distintos y llega al SQL como listas paralelas (ADR 0021, ADR 0022).

## Consecuencias

- `additions` queda con 4 columnas: `contract_id`, `addition_type`, `is_value_addition`, `registered_date`.
- La prueba golden fija 15.884 filas, 5.990 contratos, 642 adiciones en el valor, 0 filas en `other` y 0 sin fecha.
- Si la conciliación con MEData muestra que otro tipo trae valor, solo cambia el catálogo y esta decisión.
