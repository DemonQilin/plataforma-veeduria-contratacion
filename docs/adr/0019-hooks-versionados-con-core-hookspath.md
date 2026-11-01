# 0019. Hooks de git versionados con `core.hooksPath` y verificación en la CI

- **Estado:** Aceptada
- **Fecha:** 2026-11-01
- **Fuente:** [CLAUDE.md](../../CLAUDE.md#comandos)

## Contexto

Cada `CLAUDE.md` tiene un `AGENTS.md` con el mismo contenido, para los agentes que leen uno u otro. Se desfasaron: `pipeline/AGENTS.md` no recibió la actualización de la tarea 5. Hace falta una verificación que lo impida.

Git no versiona `.git/hooks/` ni instala hooks al clonar, y `--no-verify` los salta. Además, GGA instala su propio hook de pre-commit en `.git/hooks/`, que `core.hooksPath` deja de leer.

## Decisión

- **`scripts/check-agents-sync.sh` es la única implementación.** Compara, en el índice de git, cada `CLAUDE.md` con el `AGENTS.md` de su carpeta; falla si difiere o falta. Compara el índice y no el árbol de trabajo, para que valga lo que se va a confirmar.
- **Hook versionado en `.githooks/pre-commit`,** que llama a `gga run` (solo si `gga` está instalado) y luego al script. Se activa una vez por clon con `git config core.hooksPath .githooks`, o con `mise run setup`.
- **La CI corre el mismo script** en cada `push` y `pull_request`, y `mise run check` lo incluye. Es la única garantía que alcanza a quien no active el hook o lo salte.

## Consecuencias

- Los cambios al hook llegan con `git pull`; no hay copias instaladas que se desfasen.
- La activación es un paso manual por clon. Sin ella, la CI es la que avisa.
- Con `core.hooksPath` activo, el hook de `.git/hooks/pre-commit` que instala GGA no se ejecuta; `.githooks/pre-commit` lo reemplaza.
- Un `AGENTS.md` o `CLAUDE.md` nuevo en otra carpeta queda cubierto sin tocar el script.

## Alternativas

- **Gestor de hooks (`pre-commit`, lefthook):** descartada. Agrega una herramienta para un solo chequeo.
- **Script que escribe en `.git/hooks/pre-commit`:** descartada. La copia instalada no se actualiza con `git pull`.
- **Hacer `AGENTS.md` un enlace simbólico a `CLAUDE.md`:** descartada. Los enlaces simbólicos fallan en Windows sin permisos de administrador, y el equipo trabaja en Windows (ver [0014](0014-finales-de-linea-lf-y-verificacion-de-deriva-en-script.md)).
