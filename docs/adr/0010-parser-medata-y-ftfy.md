# 0010. Parser propio para MEData y reparación de codificación con `ftfy`

- **Estado:** Aceptada
- **Fecha:** 2026-10-30
- **Fuente:** [docs/fuentes.md](../fuentes.md#9-problemas-de-calidad-conocidos-y-tratamiento)

## Contexto

El CSV de MEData · Ejecución contractual histórico tiene tres problemas de calidad, que son de naturaleza distinta:

- **Estructural:** cada línea viene envuelta en comillas, con comillas escapadas de forma irregular dentro. Un lector de CSV estándar desalinea las columnas o descarta filas.
- **Estructural:** 2.083 filas (8 %) vienen cortadas en origen después de la columna 28. Conservan contrato, fecha, modalidad, causal y secretaría, pero pierden valores, estado y enlace.
- **De contenido:** las tildes están rotas por doble codificación UTF-8 (*mojibake*).

Además, el archivo contiene nombres y cédulas de contratistas y supervisores, y solo se puede descargar completo. Para escribir una copia sin datos personales (ver [0007](0007-lista-blanca-unica.md)) primero hay que separar las columnas.

## Decisión

- **Los problemas estructurales se resuelven en la extracción, con un parser propio.** Es necesario ahí porque, sin separar las columnas, no se pueden descartar los datos personales antes de escribir la copia.
  - Las filas truncadas se aceptan, se completan con vacíos y se marcan con una columna `truncated`, para reportar el porcentaje.
  - Una fila que no tenga 28 columnas ni el total esperado detiene la extracción con un error que indica el número de línea, sin mostrar su contenido.
- **La codificación se repara en la normalización, con `ftfy`.** La copia queda fiel a la fuente (ver [0006](0006-snapshot-csv-con-manifest.md)) y la reparación es una regla visible y probada.
  - Se aplica solo la reparación de codificación (`ftfy.fix_encoding` o una configuración equivalente), no las demás normalizaciones que `ftfy` hace por defecto, como cambiar comillas tipográficas.
  - La reparación ocurre antes del mapeo a catálogos, para que «SecretarÃ­a» y «Secretaría» caigan en el mismo valor.
- **Pruebas sobre líneas reales:** entre 15 y 20 líneas problemáticas del archivo se convierten en fixtures, con nombres y cédulas reemplazados por valores falsos antes de guardarlas. Una prueba adicional, marcada `network`, recorre el archivo completo y verifica el conteo de filas y de truncadas (2.083).

## Consecuencias

- La copia de MEData contiene solo columnas permitidas y valores tal como vienen de la fuente, con las tildes rotas incluidas.
- El jurado ve la reparación de codificación como un paso del pipeline, no como un dato ya limpio de origen.
- El parser es código propio que hay que mantener; si MEData cambia el formato, la extracción falla de forma explícita.
- El 8 % de filas truncadas se puede usar para conteos, fechas, modalidad y secretaría, pero no para valores. El reporte de calidad lo dice.

## Alternativas

| Criterio | Parser propio + `ftfy` en normalización (elegida) | Lector estándar con opciones permisivas | Reparación manual de codificación |
|---|---|---|---|
| Comillas irregulares | Resueltas con reglas probadas | Columnas desalineadas o filas descartadas | No aplica |
| Filas truncadas | Marcadas y conservadas | Descartadas o desalineadas | No aplica |
| Mojibake | `ftfy` detecta qué texto está roto | No aplica | Falla con texto ya correcto o mezclado |

- **`csv` de Python o `read_csv` de DuckDB con opciones permisivas:** descartada. Con este archivo, las opciones como `ignore_errors` descartan filas en silencio, justo lo que no se puede permitir.
- **`texto.encode("latin-1").decode("utf-8")`:** descartada. Funciona con el texto roto, pero falla o empeora el texto que ya estaba bien; `ftfy` detecta qué reparar.
- **Reparar la codificación en la extracción:** descartada porque la copia dejaría de ser fiel a la fuente y la regla quedaría fuera de lo que reproduce el jurado.