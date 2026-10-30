# Documentación · Veeduría de contratación de la Alcaldía de Medellín

Hackathon de Datos 2026 · ITM

Esta carpeta reúne el diseño del proyecto: qué se construye, con qué datos, con qué reglas y por qué. Está escrita para el equipo, el jurado y cualquier persona que quiera reproducir o revisar el análisis. Claude Code también la usa: los archivos `CLAUDE.md` del repositorio indican qué documento leer según la tarea.

## Documentos

| Documento | Qué contiene | Léelo cuando… |
|---|---|---|
| [`producto.md`](producto.md) | Propósito, pregunta, hallazgo titular, alcance, tablero, ética, privacidad, guía de lenguaje y siguientes etapas | Necesites entender qué se construye y para quién, o escribas textos del tablero |
| [`fuentes.md`](fuentes.md) | Conjuntos de datos, campos, llaves de cruce, lista blanca de columnas, problemas de calidad y calendario de la Ley de Garantías | Trabajes en la extracción o dudes de dónde sale un campo |
| [`reglas.md`](reglas.md) | Flujo del pipeline, conceptos del dominio, catálogos, reglas R1–R17, decisiones de dominio D1–D5, salidas y pruebas | Trabajes en normalización, consolidación, cruce o publicación |
| [`indicadores.md`](indicadores.md) | Indicadores I1–I8 y metodología del hallazgo titular, con su criterio de decisión y limitaciones | Calcules un indicador o interpretes una cifra |
| [`plan.md`](plan.md) | Cronograma, prioridades, puntos de decisión, riesgos, mapa contra la rúbrica, entregables y borrador de `instrucciones.txt` | Planees el trabajo o prepares la entrega |
| [`bitacora.md`](bitacora.md) | Observaciones fechadas de la exploración de datos, con cifras, y preguntas abiertas | Necesites saber qué se observó, cuándo y con qué datos |
| [`adr/`](adr/) | Un registro por decisión técnica (ADR) | Quieras cambiar una herramienta o un enfoque, o saber por qué algo es como es |

## Cómo se relacionan

- **`producto.md` dice qué y para quién; `reglas.md` e `indicadores.md` dicen cómo se calcula; `fuentes.md` dice con qué datos.**
- **La bitácora registra lo observado; los demás documentos registran lo decidido.** Cuando una observación produce una decisión, la decisión pasa al documento que corresponde (una regla a `reglas.md`, una decisión técnica a `adr/`) y la bitácora conserva la observación con su fecha.
- **La lista blanca de columnas tiene dos lugares que deben coincidir:** `fuentes.md` explica qué columnas se usan y por qué, y `pipeline/sources.toml` las implementa. Se cambian siempre juntos, en el mismo commit.

## Identificadores estables

Estos identificadores se citan en el código, en las pruebas y en los archivos SQL. No se renumeran ni se reutilizan: si una regla se elimina, su número queda retirado.

| Prefijo | Qué identifica | Dónde se define |
|---|---|---|
| R1–R17 | Reglas de negocio | `reglas.md` |
| D1–D5 | Decisiones de dominio | `reglas.md` |
| I1–I8 | Indicadores | `indicadores.md` |
| ADR 0001… | Decisiones técnicas | `adr/` |

## ADR

Cada decisión técnica vive en su propio archivo dentro de `adr/`, con el formato `NNNN-titulo-en-minusculas.md` y un número consecutivo de cuatro dígitos.

```markdown
# NNNN. Título de la decisión

- **Estado:** Propuesta | Aceptada | Reemplazada por [NNNN](NNNN-titulo.md)
- **Fecha:** AAAA-MM-DD
- **Fuente:** [docs/documento.md](../documento.md#seccion)

## Contexto

Qué problema había y qué restricciones pesaban.

## Decisión

- Qué se decidió, en viñetas concretas y verificables.

## Consecuencias

- Qué se gana, qué se pierde y qué queda obligado a partir de ahora.

## Alternativas

Tabla comparativa cuando hay criterios comunes, y una viñeta por alternativa
descartada con el motivo.
```

- **Fuente** enlaza la sección de `docs/` donde se aplica la decisión.
- Los ADR se citan entre sí con enlaces relativos: `[0004](0004-contrato-pydantic-json-schema-ts.md)`.
- Un ADR aceptado no se edita para cambiar la decisión. Si la decisión cambia, se escribe uno nuevo que reemplaza al anterior, y el anterior pasa a estado «Reemplazada por NNNN».

## Convenciones

- **Idioma:** la documentación está en español. El código está en inglés, según el glosario del `CLAUDE.md` de la raíz.
- **Fechas:** formato `29 oct 2026` en el texto y `2026-10-29` en nombres de archivo y metadatos.
- **Cifras:** separador de miles con punto y decimales con coma (`1.390`, `52,3 %`), siempre con su base.
- **Actualización:** si cambias una regla, un indicador o una decisión, actualiza su documento en el mismo commit que el código.

## Este repositorio es público

Todo lo que entra a `docs/` queda publicado. Antes de agregar algo, verifica que no contenga datos personales, respuestas privadas de los organizadores ni información entregada bajo confidencialidad.