# 0004. Contrato de datos: Pydantic → JSON Schema → TypeScript

- **Estado:** Aceptada
- **Fecha:** 2026-10-29
- **Fuente:** [docs/reglas.md](../reglas.md#7-salidas-que-consume-el-tablero)

## Contexto

`data/outputs/` es la frontera entre el pipeline en Python y el tablero en TypeScript (ver [0001](0001-monorepo-pipeline-web-data.md)). Si un campo cambia de nombre en Python y el tablero lo sigue leyendo con el nombre viejo, el resultado es un gráfico vacío, no un error, y puede aparecer justo en la demostración.

Los datos los produce el pipeline, así que es ahí donde se sabe qué forma tienen. El tablero solo los presenta (ver [0005](0005-dominio-solo-en-python.md)).

## Decisión

- **Los modelos de Pydantic de `pipeline/src/veeduria/publish/` son la única fuente de verdad del contrato.**
- **El pipeline valida al escribir.** Cada salida se construye con su modelo; si algo no cumple, la ejecución falla antes de tocar `data/outputs/`.
- **`mise run contract` genera el resto:**
  1. Exporta un JSON Schema por salida a `data/schema/`.
  2. Genera `web/src/types/contract.ts` con `json-schema-to-typescript`.

  Ambos archivos se versionan y nunca se editan a mano.
- **La integración continua regenera el contrato y falla si `git diff` muestra cambios.** Nadie puede cambiar un modelo sin actualizar el contrato.
- **El tablero no vuelve a validar.** No hay Zod ni Ajv en el build: los datos ya llegan validados.
- **`web/src/lib/data.ts` es el único archivo que importa desde `../data/outputs`.** Asigna los tipos del contrato una sola vez y exporta funciones al resto del sitio.
- `web/` usa `astro/tsconfigs/strictest`, y la integración continua ejecuta `astro check`.

## Consecuencias

- Un campo renombrado o eliminado rompe `astro check` en vez de producir un gráfico vacío.
- Cambiar un modelo exige, en el mismo commit, regenerar el contrato y ajustar `data.ts`.
- `data/schema/` documenta el formato de las salidas para cualquiera que quiera reutilizarlas, como un periodista o una veeduría, sin leer el código.
- La generación cruza las dos bases: la exportación corre con `uv run` y la generación de tipos con `pnpm`. `mise run contract` las encadena; el camino nativo son dos comandos.
- La asignación de tipos en `data.ts` confía en que `data/outputs/` solo lo escribe el pipeline. Una edición a mano de un JSON no la detectaría el build; la integración continua sí, porque regenera las salidas.

## Alternativas

| Criterio | Pydantic → JSON Schema → TS (elegida) | Zod escrito a mano en `web/` | JSON Schema escrito a mano |
|---|---|---|---|
| Fuentes de verdad | Una: los modelos de Pydantic | Dos: modelos y esquemas de Zod | Una, pero hay que generar también los modelos de Python |
| Validación | Al escribir, en el pipeline | Al escribir y al leer | Depende de lo que se genere |
| Herramientas extra | `json-schema-to-typescript` | Zod | Generadores en ambos lados |
| Ergonomía | Python y TypeScript idiomáticos | Idiomática en ambos | JSON Schema es verboso de escribir |

- **Zod escrito a mano:** descartada porque mantiene dos definiciones del mismo contrato que pueden divergir sin que nada lo detecte.
- **JSON Schema escrito a mano como fuente neutral:** descartada. Es la opción más simétrica, pero obliga a generar también los modelos de Python y escribir JSON Schema a mano es lento.
- **Validar también en el build con Zod o Ajv:** descartada por redundante. Duplica la validación que ya hace Pydantic, sin detectar nada que la integración continua no detecte.
- **Sin contrato, con los tipos inferidos del JSON:** descartada. TypeScript infiere tipos demasiado amplios y un cambio de nombre pasaría sin error.

La elección es reversible: si el contrato creciera, se podría agregar validación en el build sin cambiar la fuente de verdad.