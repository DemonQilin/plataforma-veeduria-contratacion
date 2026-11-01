# 0009. Extracción de SECOP II en CSV, paginada y filtrada en la API

- **Estado:** Aceptada
- **Fecha:** 2026-10-30
- **Fuente:** [docs/fuentes.md](../fuentes.md#11-notas-para-la-extracción)

## Contexto

Los conjuntos de SECOP II se consultan por la API de Socrata en datos.gov.co. Son conjuntos nacionales con millones de filas, de los que el proyecto necesita unos pocos miles. La API tiene varios comportamientos que, si no se conocen de antemano, producen datos incompletos sin ningún error:

- **Límite por defecto de 1.000 filas.** Sin `$limit`, la respuesta se corta en silencio.
- **Orden no garantizado entre páginas.** Sin `$order`, dos páginas consecutivas pueden repetir u omitir filas.
- **El JSON omite los campos nulos.** Una fila no trae la llave si el valor es nulo, así que las columnas varían entre filas.
- **Adiciones no tiene campo de entidad.** Solo se puede filtrar por `id_contrato`.
- **Límites de uso.** Sin token de aplicación, las peticiones comparten un cupo por IP.

## Decisión

- **Endpoint CSV:** se consulta `/resource/<id>.csv`, que siempre trae en el encabezado las columnas del `$select`. Coincide además con el formato de la copia (ver [0006](0006-snapshot-csv-con-manifest.md)).
- **`$select` explícito** desde `pipeline/sources.toml` (ver [0007](0007-lista-blanca-unica.md)). Nunca `$select=*`.
- **Filtros en el `$where`, no en Python:** nombre exacto de la entidad (R1) y rango de fechas. Se extrae desde el 1 de enero de 2022, el inicio de R2: los años de control de SECOP II son 2023 a 2025, y 2021 solo se usa en el Plan Anual de MEData.
- **Paginación completa:** siempre `$limit`, `$offset` y un `$order` por una llave estable (`id_contrato`, `id_del_portafolio`). Se pide hasta recibir una página incompleta. Si no hay una llave única (Procesos), se usa `:id` y la copia se ordena en local antes de escribir (ver [0016](0016-orden-determinista-de-la-copia.md)).
- **Adiciones por lotes:** `id_contrato in (…)` con lotes de 200 identificadores, para no exceder el largo máximo de la URL.
- **Robustez:** `httpx` con tiempo de espera explícito y `tenacity` con reintentos y espera exponencial ante errores 5xx, 429 y fallas de conexión.
- **Token opcional:** se envía el encabezado `X-App-Token` si existe la variable de entorno `SOCRATA_APP_TOKEN`. En GitHub Actions es un *secret*. El camino del jurado no lo necesita, porque parte de la copia.
- **Verificación al terminar:** el número de filas recibidas se compara con un `count(*)` de la misma consulta, y se registra en el manifiesto.

## Consecuencias

- Una extracción incompleta falla de forma visible en lugar de producir una copia parcial.
- Solo viajan los pocos miles de filas del Distrito, no el conjunto nacional.
- Las columnas son estables aunque una página entera tenga un campo nulo.
- Los valores del CSV llegan como texto; la conversión de tipos queda en la normalización.
- La consulta exacta queda registrada en el manifiesto, así que cualquiera puede repetirla en el navegador.

## Alternativas

| Criterio | CSV paginado con filtros en la API (elegida) | JSON paginado | Descarga completa del conjunto |
|---|---|---|---|
| Columnas estables | Sí | No: omite nulos | Sí |
| Volumen transferido | Solo el Distrito | Solo el Distrito | Todo el país |
| Lista blanca en origen | Sí, con `$select` | Sí, con `$select` | No: trae datos personales |
| Tipos | Texto | Parcialmente tipados | Texto |

- **JSON paginado:** descartada porque las columnas varían entre filas y obliga a reconstruir el esquema.
- **Descarga completa del conjunto:** descartada por volumen y porque traería todas las columnas, incluidas las personales.
- **Filtrar en Python:** descartada porque transfiere datos que no se usan y que pueden incluir otras entidades con el mismo NIT.
- **Cliente `sodapy`:** descartada. Agrega una dependencia que trabaja en JSON y no resuelve los nulos; un cliente propio con `httpx` son pocas líneas.