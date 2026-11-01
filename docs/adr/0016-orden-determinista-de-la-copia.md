# 0016. Orden determinista de la copia

- **Estado:** Aceptada
- **Fecha:** 2026-11-01
- **Fuente:** [docs/bitacora.md](../bitacora.md#1-nov-2026--orden-de-secop-ii-procesos-y-nit-de-proveedores)

## Contexto

La paginación con `$limit` y `$offset` solo es segura si el `$order` es único. En SECOP II Procesos no lo es: la pareja `id_del_portafolio`, `id_del_proceso` se repite hasta 84 veces. Tampoco hay una llave natural: aun sumando `id_adjudicacion`, `codigoproveedor` y `fecha_adjudicacion` quedan 944 grupos repetidos, el peor con 40 filas.

Socrata documenta que `$order=:id` da un orden estable al paginar, pero no dice que `:id` sobreviva a una recarga del conjunto. `:created_at` es igual en todas las filas, lo que sugiere una recarga completa; no está verificado.

El 1 nov se descargó Procesos dos veces con cada orden. El orden por la pareja y el orden por `:id` devolvieron las mismas 23.428 filas, sin faltantes ni sobrantes, y cada uno fue estable entre sus dos corridas. La pérdida de filas no se reprodujo: esta decisión es preventiva. Además, 4.061 filas son duplicados exactos en las columnas de la lista blanca.

## Decisión

- **Paginar por una llave única.** `secop_procurement_processes` usa `order_by = ":id"`. Es único (23.428 valores para 23.428 filas) y no se pide en el `$select`, así que la lista blanca no cambia.
- **Ordenar en local antes de escribir.** `write_snapshot` ordena las filas por todas sus columnas. El determinismo de la copia sale de ahí, no de la API ni de que `:id` sea estable.
- **Conservar los duplicados exactos.** La copia guarda valores crudos; la consolidación los resuelve (R5).

## Consecuencias

- Las mismas filas dan siempre el mismo archivo y el mismo SHA-256, sin importar el orden en que lleguen.
- La primera extracción tras el cambio puede alterar el SHA-256 de una copia existente sin que cambien sus datos.
- El orden es el del texto, no el numérico: `10` va antes que `9`.
- Las filas se leen completas en memoria antes de escribir. Son decenas de miles, así que cabe de sobra.
- Un error por ancho de fila cita la línea según el orden de llegada, no el del archivo final.
- Aplica a toda consulta, incluida `secop_additions`, cuyo orden tiene la misma forma.

## Alternativas

- **Buscar una llave natural:** descartada. No existe en Procesos, como muestran los grupos repetidos.
- **Confiar solo en `:id`:** descartada. No está documentado que sobreviva a una recarga, y el SHA-256 de la copia cambiaría sin que cambien los datos.
- **Ordenar en la normalización:** descartada. El manifiesto registra el SHA-256 del archivo crudo, así que ese archivo es el que debe ser reproducible.
