# 0032. `run --from-snapshot` publica las salidas con escritura atómica

- **Estado:** Aceptada
- **Fecha:** 2026-11-04
- **Fuente:** [docs/reglas.md](../reglas.md#4-reglas) (R12, R16), [ADR 0004](0004-contrato-pydantic-json-schema-ts.md), [ADR 0006](0006-snapshot-csv-con-manifest.md)

## Contexto

Las etapas (normalizar, consolidar, cruzar y conciliar) existían como funciones que solo encadenaban las pruebas. `veeduria run --from-snapshot`, el camino del jurado, seguía sin hacer nada. Los indicadores I1–I8 todavía no existen, así que el único modelo del contrato es `Metadata`.

## Decisión

- **`veeduria/pipeline.py` (`build`)** corre las etapas en memoria sobre la copia, en un orden fijo, sin red y sin escribir.
- **`run --from-snapshot` publica `data/outputs/metadata.json`:** fecha de corte (R12, la firma más reciente de `canonical_contracts`), fuentes con enlace y licencia (de la tabla `[[datasets]]` de `sources.toml`, ordenadas por nombre) y `RULES_VERSION`.
- **Escritura atómica** (`publish/outputs.py`): se escribe en una carpeta temporal junto a `data/outputs/` y se reemplaza la carpeta entera solo si todo salió bien. Un fallo deja las salidas como estaban y sale con código 1, con un mensaje que no cita filas.
- **Determinismo:** JSON con llaves ordenadas, sangría fija y LF. La integración continua corre el comando y falla si `git diff` sobre `data/outputs/` no queda vacío.
- **`--refresh` no publica:** solo actualiza la copia (ADR 0006).

## Consecuencias

- Cada indicador nuevo agrega su modelo a `CONTRACT_MODELS` y su archivo al diccionario de `write_outputs`.
- `RULES_VERSION` se sube a mano cuando una regla cambia una cifra publicada.
