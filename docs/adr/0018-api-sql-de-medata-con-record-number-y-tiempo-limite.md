# 0018. API SQL de MEData: orden por `record_number`, distribución fija y tiempo límite

- **Estado:** Aceptada
- **Fecha:** 2026-11-01
- **Fuente:** [docs/bitacora.md](../bitacora.md#1-nov-2026--plan-anual-de-adquisiciones-de-medata)

## Contexto

El Plan Anual de Adquisiciones histórico se consulta por la API SQL del portal (`/api/1/datastore/sql/`), que permite elegir columnas y evita descargar el CSV con las columnas excluidas. A diferencia de Socrata, esta API tiene tres rasgos que el ADR [0009](0009-extraccion-csv-paginada.md) no cubre:

- **Responde 504 de forma intermitente.** La ficha del conjunto falló cuatro veces seguidas y luego respondió en 0,5 s. El portal corta a los 30 s.
- **La tabla no tiene llave natural.** `ano,fecha_estimada_inicio` tiene empates, así que no sirve para paginar con `LIMIT` y `OFFSET`.
- **La distribución CSV tiene un identificador propio** (`f338ad23-…`), distinto del del conjunto (`1-028-11-000089`), y averiguarlo exige la ficha, que es justo lo que da 504.

## Decisión

- **Consulta mínima:** `[SELECT <allowed> FROM <distribución>][ORDER BY record_number ASC][LIMIT n OFFSET m];`. Nunca `SELECT *`. La lista de columnas sale de `sources.toml` (ver [0007](0007-lista-blanca-unica.md)).
- **Orden por `record_number`:** es único, acepta `ORDER BY` y no aparece en la respuesta si no se pide. Paginar de a 1.000 dio las mismas 18.764 filas que la consulta completa. Como en [0016](0016-orden-determinista-de-la-copia.md), el escritor de la copia ordena en local antes de escribir.
- **Distribución fija en `sources.toml`** (`distribution`), para no depender de la ficha en cada corrida.
- **Verificación al terminar:** las filas recibidas se comparan con `SELECT COUNT(*)`. Cada fila debe traer exactamente las columnas de la lista blanca; si no, falla citando columnas y línea, nunca valores.
- **Reintentos con tiempo límite:** 5 intentos y 300 s por petición, con espera exponencial, ante 429, 5xx y fallas de conexión. Un 400 no se reintenta.
- **Sin el token de datos.gov.co.** MEData es otro dominio: la CLI crea el cliente sin `X-App-Token`.
- **Código compartido en `extract/http.py`:** `ExtractionError`, `Extraction` y el criterio de reintento. `SocrataError` y `MedataError` heredan de `ExtractionError`.

## Consecuencias

- Una extracción incompleta falla de forma visible y la copia anterior queda intacta.
- Dos corridas seguidas dieron el mismo SHA-256, así que el orden local y el de la API no se contradicen.
- La ejecución contractual (CSV completo) no usa este cliente; reutiliza solo `extract/http.py`.
- Si el portal cambia el identificador de la distribución, la extracción falla con HTTP 400 o 404 y hay que actualizar `sources.toml`.

## Alternativas

- **Descargar el CSV completo:** descartada. Trae `nombre_del_responsable`, `telefono_del_responsable`, `correo_del_responsable` y `descripcion`, que no pueden salir de la fuente.
- **Ordenar por `ano,fecha_estimada_inicio`:** descartada. No es único, y paginar con empates puede repetir u omitir filas.
- **Pedir toda la tabla en una sola consulta:** descartada. Funciona hoy (4,5 s), pero una respuesta de 4 MB aumenta la probabilidad de un 504 sin forma de reanudar; las páginas se reintentan por separado.
- **Averiguar la distribución en cada corrida:** descartada. Depende de la ficha, que es la petición que más falla.
