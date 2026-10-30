# 0001. Monorepo con `pipeline/`, `web/` y `data/` como frontera

- **Estado:** Aceptada
- **Fecha:** 2026-10-29
- **Fuente:** [docs/reglas.md](../reglas.md#1-flujo)

## Contexto

El proyecto tiene dos bases de código en lenguajes distintos: un pipeline en Python que produce los datos y un tablero en Astro que los presenta. Las bases del concurso exigen un único repositorio público, y el jurado debe poder probarlo todo siguiendo solo `instrucciones.txt`.

Los datos pasan por niveles con requisitos de privacidad distintos: las descargas completas de MEData contienen nombres y cédulas, mientras que lo que se publica no puede contener datos personales.

## Decisión

- Un solo repositorio con dos carpetas simétricas, `pipeline/` y `web/`. Cada una tiene su propio gestor de dependencias, su lockfile y su archivo de versión.
- La raíz no contiene código: solo lo que exigen las bases (`instrucciones.txt`, `guia_entrega.pdf`, licencia), la documentación, `mise.toml` y los flujos de GitHub Actions.
- `pipeline/` y `web/` no se importan entre sí. Se comunican solo a través de `data/`:

  | Carpeta | En git | Contenido |
  |---|---|---|
  | `data/raw/` | No | Descargas completas. Puede contener datos personales |
  | `data/snapshot/` | Sí | Copia con solo las columnas de la lista blanca (ver [0006](0006-snapshot-csv-con-manifest.md)) |
  | `data/outputs/` | Sí | Salidas que consume el tablero |
  | `data/schema/` | Sí | Contrato de las salidas (ver [0004](0004-contrato-pydantic-json-schema-ts.md)) |

- El tablero lee `../data/outputs` directamente en el build. No hay una copia de las salidas dentro de `web/`.
- Sin herramientas de monorepo (Nx, Turborepo, workspaces compartidos).

## Consecuencias

- `data/outputs/` es la única fuente de verdad de lo que muestra el tablero; no hay copias que puedan quedar desactualizadas.
- El jurado ejecuta `cd pipeline` y `cd web` según el paso. `instrucciones.txt` lo indica en cada comando.
- `web/astro.config.mjs` debe permitir que el servidor de desarrollo de Vite lea fuera de `web/` (`vite.server.fs.allow`).
- La integración continua tiene un trabajo por carpeta, con las herramientas nativas de cada una (ver [0002](0002-mise-opcional-camino-nativo-primero.md)).
- Los commits que actualizan datos muestran en el diff qué cambió en `snapshot/` y `outputs/`.
- Que `data/raw/` quede fuera del repositorio depende del `.gitignore` y de la prueba de privacidad (ver [0007](0007-lista-blanca-unica.md)), no de la estructura.

## Alternativas

| Criterio | Carpetas simétricas (elegida) | `pyproject.toml` en la raíz | Dos repositorios |
|---|---|---|---|
| Comandos del jurado | Un `cd` por paso | El pipeline corre desde la raíz | Dos clones |
| Lectura de la estructura | Las dos bases al mismo nivel | Python es «el repositorio» y Node un invitado | Separación total |
| Cumple las bases | Sí | Sí | No: piden un repositorio |
| Contrato de datos | En el mismo commit que el código | En el mismo commit que el código | Cruza repositorios |

- **`pyproject.toml` en la raíz:** descartada. Le ahorra un `cd` al jurado, pero rompe la simetría y hace más difícil explicar la estructura en el pitch.
- **Dos repositorios:** descartada por las bases y porque un cambio en el contrato tendría que coordinarse entre repositorios.
- **Copiar las salidas a `web/src/data/`:** descartada. Deja `web/` autocontenido, pero crea una segunda copia de los datos que puede quedar desactualizada.
- **Herramientas de monorepo:** descartadas. Con dos paquetes en lenguajes distintos no aportan nada y serían una herramienta más para el jurado.