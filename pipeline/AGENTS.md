# pipeline/

Pipeline de datos en Python. Las convenciones generales (idioma, glosario, reglas no negociables) están en el `CLAUDE.md` de la raíz.

## Stack

- Python en la versión de `.python-version`, gestionado con `uv`. Dependencias en `pyproject.toml` y `uv.lock`.
- `duckdb` para transformar: consolidación, cruces y agregaciones.
- `httpx` y `tenacity` para la extracción, con tiempos de espera y reintentos.
- `ftfy` para reparar la codificación de MEData. Solo `ftfy.fix_encoding`, nunca `fix_text`: con su configuración por defecto, `fix_text` también cambia comillas tipográficas y otros caracteres, y alteraría los datos.
- `pydantic` para los modelos del contrato de salida.
- `typer` para la CLI.
- `pytest` y `ruff`.

No agregues pandas ni Polars: DuckDB es el único motor de transformación (ver `docs/adr/`).

## Estructura

```
pipeline/
├── sources.toml          # conjuntos, filtros y lista blanca de columnas: fuente única
├── reference/            # tablas curadas a mano: calendario electoral, catálogos
├── src/veeduria/
│   ├── cli.py            # veeduria run --from-snapshot | --refresh · veeduria export-schema
│   ├── extract/          # única etapa que usa la red; escribe data/snapshot/
│   ├── normalize/        # codificación, tipos, catálogos, renombre según el glosario
│   ├── consolidate/      # un contrato por referencia, un proceso por portafolio
│   ├── link/             # cruces por las llaves validadas
│   ├── indicators/       # I1 a I8
│   └── publish/          # modelos del contrato, supresión y escritura de data/outputs/
└── tests/
```

## Etapas

- **Solo `extract/` usa la red.** Todo lo que sigue lee de `data/snapshot/`, para que `--from-snapshot` funcione sin conexión.
- **`data/snapshot/` guarda valores crudos.** Solo columnas de la lista blanca, sin normalizar y en CSV UTF-8. La normalización ocurre después, para que el jurado reproduzca todas las reglas.
- **`manifest.json`** se escribe solo con `--refresh`: identificador del conjunto, URL, consulta, número de filas, SHA-256, fecha de extracción y fecha de corte.
- **Falla segura:** cada ejecución escribe en un directorio temporal y lo mueve a `data/outputs/` solo si todo terminó bien. Nunca dejes una salida a medias.

## Extracción

- **SECOP II (Socrata):** pide siempre el endpoint CSV (`/resource/<id>.csv`), porque el JSON omite los campos nulos.
  - Nunca uses `$select=*`. Construye el `$select` desde `sources.toml`.
  - Pagina siempre con `$limit`, `$offset` y un `$order` estable. Sin `$limit`, la API corta en 1.000 filas sin avisar. Si el orden tiene empates (Procesos), pagina por `:id`; el escritor de la copia ordena las filas por todas sus columnas (ADR 0016).
  - Filtra en el `$where`, no en Python: entidad por nombre exacto (R1) y rango de fechas.
  - Adiciones no tiene campo de entidad: consúltala con `id_contrato in (...)` en lotes de 200. Los identificadores salen de `data/snapshot/secop_contracts.csv` (`batch_source` en `sources.toml`), así que esa copia se extrae primero. Cada lote lleva su propio `count(*)`, y un lote sin adiciones es válido.
  - El token de aplicación se lee de la variable de entorno `SOCRATA_APP_TOKEN` si existe. Es opcional.
  - Al terminar, compara las filas recibidas con un `count(*)` de la misma consulta. Si no coinciden, falla sin escribir la copia.
  - `uv run veeduria extract <query_id>` descarga una consulta a `data/snapshot/`. Disponibles: `secop_contracts`, `secop_contracts_suppliers`, `secop_procurement_processes`, `secop_additions` (esta última exige la copia de `secop_contracts`) `medata_procurement_plan` y `medata_contract_execution` (MEData); para usar el token de `.env`: `uv run --env-file ../.env veeduria extract secop_contracts`. Un token inválido da HTTP 403; si pasa, vuelve a correrlo sin token.
- **MEData · Ejecución contractual:** descarga el CSV completo a `data/raw/`, que está fuera de git (`--raw-dir` cambia la carpeta).
  - El parser propio (`extract/medata_csv.py`) vive en `extract/` porque hay que separar las columnas para descartar los datos personales antes de escribir la copia. El archivo anterior de `data/raw/` solo se reemplaza si la descarga y el parseo salieron bien. No envía el token de datos.gov.co.
  - Las filas cortadas en origen, con 21 o 28 columnas, se aceptan, se completan con vacíos y se marcan con la columna `truncated`.
  - Una fila con un número de columnas inesperado detiene la extracción. El error indica el número de línea, nunca su contenido, porque puede tener datos personales.
- **MEData · Plan Anual de Adquisiciones:** se pide por la API SQL del portal, que da errores 504 (ADR 0018). `extract/medata.py` pide solo las columnas de la lista blanca, ordena por `record_number`, pagina de a 1.000, reintenta cada petición hasta 5 veces o 300 s y compara con `SELECT COUNT(*)`. No envía el token de datos.gov.co. Como el conjunto ya no se actualiza, `--refresh` solo lo vuelve a pedir si se fuerza.

## Transformación con DuckDB

- **Una regla por archivo SQL**, con el identificador en el nombre: `consolidate/r03_canonical_contract.sql`. La primera línea es un comentario en español que resume la regla y remite a `docs/reglas.md`.
- El SQL vive en archivos `.sql`, no en strings de Python. Los valores se pasan con parámetros de DuckDB, nunca con formateo de strings.
- La copia se lee como texto (`read_csv` con `all_varchar = true`) y los tipos se asignan de forma explícita en `normalize/`.
- La reparación de codificación (`ftfy.fix_encoding`) ocurre en `normalize/`, antes del mapeo a catálogos.
- La base de DuckDB vive en memoria. Para depurar se puede escribir en un archivo dentro de `data/raw/`, nunca en otra carpeta.
- Los catálogos y el calendario electoral se leen de `reference/` (R10). No se infieren de los datos.

## Determinismo

- Todo `SELECT` cuyo resultado termina en un archivo lleva `ORDER BY` completo.
- Redondeo explícito en `publish/`. JSON con llaves ordenadas y separadores fijos.
- La fecha de corte es la fecha de firma más reciente en la copia (R12). No uses la fecha actual en ninguna salida de `data/outputs/`.

## Contrato con el tablero

- Los modelos de Pydantic de `publish/` son la fuente de verdad del contrato.
- `uv run veeduria export-schema` exporta `data/schema/*.json`; luego `pnpm gen:types`, en `web/`, regenera `web/src/types/contract.ts`. `mise run contract` encadena ambos. La integración continua falla si eso produce cambios.
- Si cambias un modelo, regenera el contrato y ajusta `web/src/lib/data.ts` en el mismo commit.
- La supresión de celdas con menos de 5 contratos (R13) se aplica en `publish/`, antes de escribir. El tablero nunca recibe una cifra sin suprimir.

## Pruebas

- Los nombres citan la regla o el indicador: `test_r03_first_signed_date_wins`, `test_i2_window_2022`.
- **Catálogos:** cada texto crudo conocido cae en su categoría y uno desconocido cae en «Otra».
- **Golden:** cifras conocidas, como 723 contratos en SECOP II frente a 727 en MEData para enero de 2022.
- **Privacidad:** se escribe antes que la extracción y verifica que:
  - las columnas de cada CSV de `data/snapshot/` están en la lista permitida de `sources.toml`;
  - ninguna columna excluida en `sources.toml` aparece en `data/snapshot/` ni en `data/outputs/`;
  - las listas permitida y excluida no se cruzan;
  - `data/raw/` está ignorado por git;
  - ninguna celda publicada tiene menos de 5 contratos.
- **Fixtures:** filas reales recortadas, con nombres y documentos reemplazados por valores falsos antes de guardarlas. El repositorio es público.
- Las pruebas no usan la red. Las que la necesitan llevan la marca `network` y se excluyen por defecto.

## Comandos

- `uv run pytest` · `uv run pytest -m network` (solo cuando haga falta)
- `uv run ruff check` · `uv run ruff format`
- `uv run veeduria run --from-snapshot` · `uv run veeduria run --refresh`
- `uv run veeduria export-schema` después de cambiar un modelo de `publish/`
- `uv export --format requirements-txt -o requirements.txt` después de cambiar dependencias; la integración continua verifica que coincida con `uv.lock`