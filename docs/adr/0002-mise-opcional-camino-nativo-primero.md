# 0002. mise opcional, camino nativo primero

- **Estado:** Aceptada
- **Fecha:** 2026-10-29
- **Fuente:** [docs/plan.md](../plan.md#92-borrador-de-instruccionestxt)

## Contexto

El desarrollo usa mise para instalar uv, Node y pnpm con las versiones exactas del proyecto. Pero el jurado prueba el artefacto en su propio computador, posiblemente con Windows, siguiendo solo `instrucciones.txt`. Si ese paso falla, el proyecto no se califica.

La decisión del Bloque B ya establecía que el proyecto no debe depender de mise. Se revisó con estos hechos:

- **A favor de mise:** un solo instalador deja todas las versiones exactas, frente a dos instalaciones (uv y Node) por el camino nativo.
- **Lo que mise no aporta:** uv ya instala la versión exacta de Python fijada en `.python-version`. El valor real de mise se reduce a Node y pnpm, y en la modalidad de Visualización el jurado ve el resultado principalmente en el enlace publicado.
- **El costo para el jurado:** en un repositorio recién clonado, mise pide confiar en el `mise.toml` (`mise trust`), y sin `mise run` o `mise exec` exige activar el shell. Windows es su plataforma menos recorrida, y es una herramienta que el jurado probablemente no conoce.

## Decisión

- **Las versiones viven en los archivos nativos:** `pipeline/.python-version`, `pyproject.toml` y `uv.lock`; `web/.node-version`, `package.json` (`engines` y `packageManager`) y `pnpm-lock.yaml`.
- **`mise.toml` es una capa de conveniencia.** Fija las versiones de uv, Node y pnpm, y define tareas (`pipeline`, `refresh`, `contract`, `dev`, `build`, `preview`, `check`). Cada tarea es un envoltorio delgado que solo llama a `uv run` o `pnpm`. Para Node, mise lee `web/.node-version` en lugar de repetir la versión.
- **`instrucciones.txt` documenta dos caminos, en este orden:**
  - **Opción A (recomendada):** uv y Node, con pnpm ejecutado por `npx` (ver [0003](0003-pnpm-sin-corepack.md)).
  - **Opción B:** mise, con `mise trust`, `mise install` y `mise run`. Nunca depende de activar el shell.
- **La integración continua prueba ambos caminos.** El trabajo principal usa las acciones nativas (`astral-sh/setup-uv`, `actions/setup-node`, `pnpm/action-setup`) y ejecuta los comandos exactos de la opción A en Ubuntu y Windows. Un trabajo adicional ejecuta la opción B.
- Sin Makefile ni `justfile`.

## Consecuencias

- El requisito habilitante «funciona siguiendo solo `instrucciones.txt`» se vuelve a probar en cada push, incluido Windows.
- El jurado lee primero el camino con menos pasos que pueden sorprender, aunque requiera dos instalaciones.
- Mantener dos caminos cuesta cerca de una hora, más el tiempo de un trabajo adicional en la integración continua.
- Cualquier cambio en un comando de `instrucciones.txt` debe reflejarse en los flujos de GitHub Actions, y al revés.
- Si una tarea de mise hace algo más que llamar a `uv` o `pnpm`, la opción A deja de ser equivalente. La regla es que no lo haga.

## Alternativas

| Criterio | Nativo primero, mise opcional (elegida) | mise obligatorio | Solo nativo |
|---|---|---|---|
| Instalaciones para el jurado | uv y Node (A) o solo mise (B) | Solo mise | uv y Node |
| Pasos que pueden sorprender | Pocos en A | `mise trust`, activación, Windows | Pocos |
| Versiones exactas de Node y pnpm | Sí en B; pnpm exacto también en A | Sí | pnpm exacto; Node dentro del rango de `engines` |
| Comodidad en desarrollo | Tareas de mise | Tareas de mise | Comandos largos o scripts propios |
| Caminos que mantener | Dos | Uno | Uno |

- **mise obligatorio:** descartada. Concentra el riesgo en una herramienta que el jurado no conoce, justo en un requisito habilitante.
- **Solo nativo:** descartada. Pierde la comodidad de las tareas en desarrollo y la opción de un solo instalador para quien la prefiera.
- **Makefile o `justfile` como punto de entrada:** descartada. `make` es incómodo en Windows y ambos agregan una herramienta más; `uv run` y `pnpm` funcionan igual en los tres sistemas operativos.