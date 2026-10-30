# 0013. Python con uv para el pipeline

- **Estado:** Aceptada
- **Fecha:** 2026-10-29
- **Fuente:** [docs/reglas.md](../reglas.md#1-flujo)

## Contexto

El pipeline descarga, limpia, cruza y agrega datos de compras públicas, y debe poder ejecutarse en el computador del jurado siguiendo solo `instrucciones.txt`. El stack principal del equipo es TypeScript, así que escribir el pipeline en Node era una opción real.

Para el gestor de Python pesaba sobre todo la reproducibilidad: el jurado puede no tener Python instalado, o tener otra versión, y puede usar Windows.

Las decisiones de alcance y periodo del mismo bloque de decisiones (sector central, de enero de 2022 a la fecha de corte) son de producto y están en [`producto.md`](../producto.md#2-alcance).

## Decisión

- **El pipeline se escribe en Python.**
- **uv gestiona el proyecto:** instala la versión de Python fijada en `pipeline/.python-version`, resuelve las dependencias de `pyproject.toml` y las fija en `uv.lock`.
- **Los comandos del pipeline se ejecutan con `uv run`**, sin activar entornos virtuales a mano.
- **Se exporta `pipeline/requirements.txt`** con `uv export --format requirements-txt` como alternativa para quien use `pip`. Se regenera cada vez que cambian las dependencias.
- uv se instala con mise en desarrollo, pero el proyecto no depende de mise (ver [0002](0002-mise-opcional-camino-nativo-primero.md)).

## Consecuencias

- El jurado solo necesita instalar uv: con `uv sync` obtiene la versión exacta de Python y de cada dependencia, en los tres sistemas operativos.
- Hay acceso directo a las librerías que el pipeline necesita: DuckDB, Pydantic, `ftfy`, `httpx`.
- Python es el lenguaje que el jurado de un hackathon de datos espera ver en un pipeline, lo que facilita la revisión del código.
- El proyecto tiene dos lenguajes. El contrato de datos es lo que los mantiene alineados (ver [0004](0004-contrato-pydantic-json-schema-ts.md)).
- `requirements.txt` es una segunda lista de dependencias que puede quedar desactualizada; la integración continua verifica que coincida con `uv.lock`.

## Alternativas

| Criterio | Python con uv (elegida) | TypeScript con Node | Python con pip y venv | Python con Poetry |
|---|---|---|---|---|
| Instala la versión de Python | Sí | No aplica | No | No |
| Lockfile | Sí | Sí | No | Sí |
| Ecosistema de datos | Amplio | Limitado | Amplio | Amplio |
| Pasos para el jurado | Instalar uv | Instalar Node | Instalar Python, crear entorno, instalar | Instalar Python y Poetry |
| Un solo lenguaje en el repositorio | No | Sí | No | No |

- **TypeScript con Node:** descartada. Tendría un solo lenguaje y es el stack principal del equipo, pero el ecosistema de datos es más limitado (por ejemplo, no hay un equivalente directo de `ftfy`) y el pipeline perdería legibilidad para un jurado de datos.
- **pip y venv:** descartada porque el jurado tendría que instalar la versión correcta de Python a mano y no hay lockfile. Se mantiene solo como alternativa con `requirements.txt`.
- **Poetry:** descartada porque no instala Python y agrega una herramienta sin ventajas sobre uv para este proyecto.
- **conda:** no se evaluó; es pesada para un proyecto de este tamaño.