# 0006. Copia de datos en CSV, sin normalizar y con manifiesto

- **Estado:** Aceptada
- **Fecha:** 2026-10-30
- **Fuente:** [docs/reglas.md](../reglas.md#1-flujo)

## Contexto

El jurado debe poder reproducir el análisis sin depender de las APIs de datos.gov.co y de MEData, que pueden fallar durante la evaluación (MEData ya respondió con errores 504). Para eso el repositorio necesita una copia de los datos de entrada.

Esa copia tiene requisitos que pesan más que el rendimiento:

- **Privacidad:** no puede contener datos personales, aunque las descargas completas sí los tengan.
- **Reproducibilidad completa:** el jurado debe ejecutar todas las reglas de negocio, no solo los cálculos finales.
- **Transparencia:** un ciudadano o un periodista debería poder abrirla sin herramientas especiales.
- **Volumen pequeño:** unos 7.500 contratos del Distrito entre 2022 y 2026, y unas 20.000 filas de procesos.

## Decisión

- `data/snapshot/` es la salida de la extracción: **solo las columnas de la lista blanca** (ver [0007](0007-lista-blanca-unica.md)) y **los valores tal como vienen de la fuente**, sin normalizar. Las tildes rotas de MEData se conservan; se reparan en la normalización.
- **Un archivo CSV por consulta**, en UTF-8, separado por comas, con encabezado y finales de línea LF. Las filas se ordenan por una llave estable para que los diffs entre actualizaciones sean legibles.
- **Los valores se leen como texto** y los tipos se asignan de forma explícita en la normalización, donde la conversión se prueba.
- **`data/snapshot/manifest.json`** registra, por fuente: identificador del conjunto, URL, consulta exacta, número de filas, SHA-256 del CSV, fecha de extracción y fecha de corte. Para MEData también registra el SHA-256 del archivo descargado, para detectar si la fuente cambió.
- **Solo `--refresh` escribe la copia.** `--from-snapshot` la lee y nunca la modifica.
- **El Plan Anual de Adquisiciones** ya no se actualiza en MEData, así que su copia es en la práctica la fuente canónica. `--refresh` solo lo vuelve a pedir si se fuerza de forma explícita.

## Consecuencias

- El jurado reproduce todas las reglas, desde la normalización, sin conexión.
- Cualquier persona puede abrir la copia en una hoja de cálculo. En Excel para Windows, un CSV UTF-8 sin BOM puede mostrar mal las tildes si se abre con doble clic; `instrucciones.txt` indica importarlo desde «Datos > Desde texto/CSV».
- Los commits de actualización muestran en el diff qué filas cambiaron, por ejemplo registros tardíos de SECOP II.
- Se pierden los tipos en disco: la normalización debe declararlos todos, y una conversión mal declarada falla en las pruebas, no en silencio.
- El repositorio crece con cada actualización, pero a este volumen son pocos megabytes por versión.
- La fecha de extracción del manifiesto cambia en cada `--refresh`, pero no llega a `data/outputs/`, así que no rompe el determinismo.

## Alternativas

| Criterio | CSV crudo (elegida) | Parquet | JSON de la API | Base DuckDB o SQLite |
|---|---|---|---|---|
| Diff legible en git | Sí | No | Sí, pero ruidoso | No |
| Se abre sin herramientas | Sí | No | Parcialmente | No |
| Conserva tipos | No | Sí | Parcialmente | Sí |
| Columnas estables | Sí | Sí | No: Socrata omite los campos nulos | Sí |
| Tamaño | Pequeño a este volumen | Menor | Mayor | Pequeño |

- **Parquet:** descartada. Es la opción natural a gran escala, pero a este volumen sus ventajas (tipos y compresión) no compensan perder los diffs y la apertura en una hoja de cálculo. Era la recomendación inicial y se cambió por eso.
- **JSON de la API:** descartada porque Socrata omite las llaves de los campos nulos, así que las columnas varían entre filas.
- **Archivo de base de datos:** descartada por ser binario en git y requerir una herramienta para abrirlo.
- **Copia ya normalizada:** descartada porque el jurado no ejecutaría las reglas de normalización y una parte del método quedaría sin reproducir.
- **Sin copia:** descartada porque haría depender la evaluación de la disponibilidad de las APIs.