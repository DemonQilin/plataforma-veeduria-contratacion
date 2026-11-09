# Veeduría de contratación · Alcaldía de Medellín

Tablero ciudadano que muestra cómo la Alcaldía de Medellín concentra su contratación directa alrededor de la Ley de Garantías, con indicadores estándar de riesgo en compras públicas. Los indicadores son señales para revisar, no veredictos.

Proyecto del Hackathon de Datos 2026 (ITM), modalidad Visualización. Los datos vienen de SECOP II y MEData.

**Tablero en línea:** <https://demonqilin.github.io/plataforma-veeduria-contratacion/>

**Hallazgo:** en 2022 y 2026, más de la mitad de la contratación directa se firmó en enero (58,3 % y 65,3 %, frente a entre 18,6 % y 30,7 % en los años sin restricción). Cifras con fecha de corte del 30 de octubre de 2026.

Para el jurado: los pasos de prueba están en [`instrucciones.txt`](instrucciones.txt) y la guía de entrega en `guia_entrega.pdf`.

## Estructura

| Carpeta | Contenido |
|---|---|
| `pipeline/` | Pipeline en Python: extracción, normalización, consolidación, cruce, indicadores y publicación |
| `web/` | Tablero estático en Astro. Solo presenta lo que hay en `data/outputs/` |
| `data/` | `snapshot/` (copia de las fuentes sin datos personales), `outputs/` (salidas del pipeline) y `schema/` (contrato) |
| `docs/` | Diseño, reglas y decisiones. Empieza por [`docs/README.md`](docs/README.md) |

## Ejecutarlo

Los pasos para reproducir el análisis están en `instrucciones.txt`. Versión corta, con [uv](https://docs.astral.sh/uv/) y Node.js:

```
cd pipeline
uv sync
uv run veeduria run --from-snapshot
```

## Licencias

- **Código:** MIT (ver [`LICENSE`](LICENSE)).
- **Datos (`data/`) y textos del tablero:** CC BY-SA 4.0 (ver [`LICENSE-DATA`](LICENSE-DATA) y [`docs/producto.md`](docs/producto.md#47-licencias)).
