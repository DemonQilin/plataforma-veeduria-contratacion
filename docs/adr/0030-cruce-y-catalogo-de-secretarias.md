# 0030. Cruce de contratos con procesos y MEData, y catálogo de secretarías

- **Estado:** Aceptada
- **Fecha:** 2026-11-03
- **Fuente:** [docs/reglas.md](../reglas.md#4-reglas) (R7, R8, D3), [ADR 0020](0020-catalogo-de-modalidades-en-toml.md), [ADR 0028](0028-normalizacion-de-medata-ejecucion.md), [ADR 0029](0029-consolidacion-de-contratos-y-procesos.md)

## Contexto

R8 asigna la secretaría con la de MEData y, si no, con la unidad del proceso en SECOP II. Las dos fuentes escriben la secretaría con vocabularios distintos: MEData usa 28 abreviaturas («Gest Hum yServ Ciu», «Incl.Social y Flia») y SECOP II 41 variantes, con mayúsculas, prefijos y siglas que cambian entre años («SECRETARÍA SUMINISTROS Y SERVICIOS», «SUMINISTROS Y SERVICIOS», «DAGRED», «DAGRD»). Sin unificarlas, el explorador y las páginas por secretaría mostrarían la misma secretaría dos veces.

MEData trae una línea por cambio del contrato: 25.783 líneas de 2.939 contratos. En ningún contrato cambian la secretaría, la fecha de firma, los valores, la duración ni el estado entre sus líneas. Las 2.072 líneas truncadas conservan la secretaría pero no los valores, y 54 contratos tienen todas sus líneas truncadas.

## Decisión

- **Catálogo `pipeline/reference/departments.toml`**, con el formato de los demás catálogos. Cada secretaría tiene un código en inglés, una etiqueta en español y los textos crudos de las dos fuentes, comparados sin mayúsculas, tildes ni espacios. Un texto repetido hace fallar la carga.
  - Un texto que el catálogo no reconoce **no cae en un valor por defecto**: `classify_department` devuelve `None`, R8 pasa a la fuente siguiente y el texto queda en `quality_issues`. Así una abreviatura nueva de MEData no oculta la unidad válida de SECOP II.
  - Equivalencias que no son obvias por el nombre, a revisar con quien conozca la estructura de la Alcaldía: «De la No Violencia» (MEData) con «Secretaria de Paz y Derechos Humanos» (SECOP II); «Gest y ContrTerrit» con «Secretaria Gestión y Control»; «Gobierno y GestGab» con «Secretaría de Gobierno»; «Gest Hum yServ Ciu» con «Secretaria Gestión Humana»; «Contratación Dagrd» con DAGRD.
  - «Buen Comienzo» es un programa que las dos fuentes usan como unidad; se trata como una más. «Alcaldía» solo aparece en MEData y «Turismo y Entretenimiento» solo en SECOP II.
- **`medata_contracts`**: una fila por contrato. Los valores salen con `max()`, que ignora las líneas truncadas porque tienen valores nulos. `truncated` es verdadero solo si todas sus líneas lo están. Se omiten programa y causal, que varían dentro del contrato y R8 no usa.
- **`linked_contracts`**: un contrato canónico por fila, con el proceso y MEData unidos por `LEFT JOIN`, así que ningún contrato se pierde por no tener proceso o no estar en MEData.
  - **R8:** `department` es el código del catálogo según MEData; si no, según la unidad del proceso; si no, `unassigned`. `department_source` guarda de cuál salió.
  - **D3:** `final_value` es el de MEData si existe; si no, el de SECOP II. `total_addition_value` solo viene de MEData.
  - **R7:** `is_value_eligible` es falso para `public_credit`. La fila se conserva, así que cuenta en los conteos, y los indicadores de valor filtran por esta marca.
- `quality_issues` recibe los textos sin mapear (`reason=unmapped_department_text`) y los contratos sin secretaría (`reason=no_department`). El porcentaje de «Sin asignar» sale de contar estos últimos sobre `linked_contracts`.

## Consecuencias

- Con la copia: 7.428 contratos, 2.632 con MEData, 11 de crédito público, secretaría de MEData en 2.632, de SECOP II en 4.777 y sin asignar en 19 (0,26 %).
- Un único texto queda sin mapear, «SUMINISTRO DE VESTIDO Y CALZADO DE LABOR», que es el nombre de un proceso escrito en el campo de la unidad. Ningún contrato depende de él.
- Si una equivalencia del catálogo resulta incorrecta, se corrige en un archivo TOML sin tocar código.
- La conciliación de R15 (tarea 9) parte de `in_medata`. Falta cablear el cruce en `run` (tarea 10).

## Alternativas

- **Texto crudo de cada fuente:** descartada. Duplica secretarías en el tablero.
- **Solo la unidad de SECOP II:** descartada. Cambia R8, deja 23 contratos sin proceso como «Sin asignar» y igual necesita limpiar 41 variantes.
- **Un valor por defecto para los textos desconocidos:** descartada. Una abreviatura nueva de MEData taparía una unidad válida de SECOP II.
- **Colapsar MEData al normalizar:** descartada en el [ADR 0028](0028-normalizacion-de-medata-ejecucion.md); el colapso va con el cruce.
