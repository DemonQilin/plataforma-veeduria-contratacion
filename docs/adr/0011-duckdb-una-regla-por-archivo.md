# 0011. DuckDB como motor de transformación, una regla por archivo SQL

- **Estado:** Aceptada
- **Fecha:** 2026-10-30
- **Fuente:** [docs/reglas.md](../reglas.md#4-reglas)

## Contexto

El pipeline consolida, cruza y agrega unos pocos miles de contratos y procesos. A este volumen el rendimiento no decide nada: cualquier motor termina en segundos. Lo que sí importa es cómo se leen y se explican las reglas.

Las reglas de consolidación y cruce son relacionales. Consolidar un contrato tomando la primera fecha de firma (R3) es una función de ventana; los cruces por llave y las agregaciones por secretaría y mes son SQL puro. Además, cada regla tiene un identificador (R1–R17) que debe poder rastrearse desde la documentación hasta el código, y el compañero de equipo apoya con tareas de código acotadas.

## Decisión

- **DuckDB es el único motor de transformación** del pipeline. No se usan pandas ni Polars.
- **Una regla por archivo `.sql`, con el identificador en el nombre:** `consolidate/r03_canonical_contract.sql`, `indicators/i2_pre_restriction_share.sql`. La primera línea es un comentario en español que resume la regla y remite a [`reglas.md`](../reglas.md) o [`indicadores.md`](../indicadores.md).
- **Python orquesta:** decide el orden de las etapas, carga los archivos SQL y pasa los parámetros. El SQL no vive en strings de Python.
- **Parámetros con el mecanismo de DuckDB**, nunca con formateo de strings.
- **La copia se lee como texto** (`read_csv` con `all_varchar = true`) y los tipos se asignan de forma explícita en la normalización (ver [0006](0006-snapshot-csv-con-manifest.md)).
- **La base vive en memoria** durante cada ejecución. Para depurar se puede escribir en un archivo dentro de `data/raw/`, que está fuera de git.
- **Toda consulta cuyo resultado se escribe en disco lleva `ORDER BY` completo**, para que la salida sea determinista.
- **Las reglas se prueban con pytest:** cada prueba carga tablas pequeñas de fixture en DuckDB, ejecuta el archivo de la regla y compara el resultado.

## Consecuencias

- Cada regla de `reglas.md` tiene un archivo con su nombre. En el pitch se puede abrir `r03_canonical_contract.sql` y leerlo en voz alta.
- Buscar «r03» en el repositorio encuentra la regla, su implementación y su prueba.
- El SQL es accesible para quien no domina Python, lo que facilita repartir trabajo.
- El soporte del editor para SQL en archivos es menor que para expresiones tipadas de Python: los errores de columnas aparecen al ejecutar, no al escribir. Las pruebas por regla lo compensan.
- La lógica de normalización que no es SQL natural, como la reparación con `ftfy` (ver [0010](0010-parser-medata-y-ftfy.md)), vive en Python y se aplica antes de cargar los datos a DuckDB o mediante funciones registradas.

## Alternativas

| Criterio | DuckDB con SQL en archivos (elegida) | Polars | pandas |
|---|---|---|---|
| Lectura de reglas relacionales | SQL directo, con funciones de ventana | Expresiones encadenadas | Métodos con semántica de índices |
| Trazabilidad por regla | Un archivo por regla | Una función por regla | Una función por regla |
| Soporte del editor | Menor | Tipado y autocompletado | Parcial |
| Accesible para el compañero | Alta | Media | Media |
| Lee y escribe CSV y Parquet | Sí | Sí | Sí |

- **Polars:** descartada por poco. Su API tipada y su soporte del editor son mejores, y habría sido igual de válida. Ganó DuckDB porque las reglas se leen como SQL y cada una cabe en un archivo con su identificador.
- **pandas:** descartada por la semántica de índices, los tipos menos estrictos y porque no aporta nada sobre las otras dos.
- **DuckDB y Polars juntos:** descartada. Dos modelos mentales para el mismo trabajo; lo importante era elegir uno solo desde la primera función.