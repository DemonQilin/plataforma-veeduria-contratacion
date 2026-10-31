# 0014. Finales de línea LF y verificación de deriva en un script

- **Estado:** Aceptada
- **Fecha:** 2026-10-30
- **Fuente:** [CLAUDE.md](../../CLAUDE.md#comandos)

## Contexto

Al estructurar el repositorio aparecieron tres puntos que los ADR [0002](0002-mise-opcional-camino-nativo-primero.md), [0004](0004-contrato-pydantic-json-schema-ts.md) y [0006](0006-snapshot-csv-con-manifest.md) dejaban abiertos:

- **Finales de línea.** El equipo trabaja en Windows con `core.autocrlf=true`. Los archivos generados (`data/schema/`, `contract.ts`, `requirements.txt`, los CSV de la copia) se escriben con LF, así que en Windows `git` los vería distintos de los de Linux y la verificación de deriva fallaría sin que nada hubiera cambiado.
- **Verificar que el contrato no derive.** `git diff` no detecta archivos nuevos sin rastrear ni distingue entre «cambió al regenerarlo» y «ya tenía cambios sin confirmar». Además, la lógica de la verificación tiene que correr igual con `mise run check`, con la integración continua y con los comandos nativos, y el `CLAUDE.md` de la raíz pide que la lógica no viva en `mise.toml`.
- **Versión de Node en `mise.toml`.** El ADR 0002 decía que mise leería `web/.node-version`. mise solo lee los archivos de versión del directorio donde está su configuración y de los directorios por encima, y `web/.node-version` está debajo de la raíz.

## Decisión

- **`.gitattributes` fija `* text=auto eol=lf`.** Todo el repositorio usa LF, en cualquier sistema operativo.
- **`pnpm check:drift` (en `web/scripts/check-drift.mjs`) es la única implementación de la verificación de deriva.** `mise run check:drift`, la integración continua y los comandos nativos llaman al mismo script. En lugar de `git diff`, calcula la huella de `data/schema/*.json`, `web/src/types/contract.ts` y `pipeline/requirements.txt`, regenera los tres y falla si alguna cambió. También verifica que:
  - `uv.lock` esté al día (`uv lock --check`);
  - la versión de pnpm sea la misma en `web/package.json`, `mise.toml` e `instrucciones.txt`;
  - la versión de Node sea la misma en `web/.node-version` y `mise.toml`.
- **`veeduria export-schema` borra los esquemas sin modelo.** Así un modelo eliminado no deja un JSON huérfano que el contrato siga publicando.
- **`mise.toml` repite la versión de Node** en lugar de leer `web/.node-version`. La fuente de verdad sigue siendo el archivo nativo; el script de deriva falla si difieren.
- **El comando de `requirements.txt` no lleva `--locked`,** porque `uv` escribe el comando en el encabezado del archivo y un comando distinto produciría un archivo distinto. La verificación de que el bloqueo está al día es el paso separado `uv lock --check`.

## Consecuencias

- La verificación de deriva funciona con cambios sin confirmar y detecta archivos nuevos, modificados y huérfanos.
- Cambiar la versión de Node exige editar dos archivos (`web/.node-version` y `mise.toml`); el script lo hace visible.
- El script depende de `uv` y de Node a la vez, algo que ya ocurre en todo el proyecto.
- Quien tenga un `.gitattributes` local que contradiga el del repositorio tendrá advertencias de finales de línea al confirmar; no afectan el contenido.

## Alternativas

- **`git diff --exit-code` después de regenerar:** descartada. No ve archivos nuevos sin rastrear y mezcla la deriva con cambios locales sin confirmar.
- **Lógica de la verificación en `mise.toml` o en el flujo de GitHub Actions:** descartada. Haría que el camino nativo y el de mise dejaran de ser equivalentes (ver [0002](0002-mise-opcional-camino-nativo-primero.md)).
- **Dejar `core.autocrlf` a cada persona:** descartada. La configuración local no viaja con el repositorio.
- **Que mise lea `web/.node-version`:** descartada. Requeriría un `.node-version` en la raíz, es decir, una segunda copia del mismo dato.
