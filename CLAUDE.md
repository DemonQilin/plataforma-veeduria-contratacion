# Veeduría de contratación · Alcaldía de Medellín

Pipeline en Python que extrae datos de SECOP II y MEData, calcula indicadores estándar de riesgo en compras públicas y publica un tablero estático en Astro para público no técnico. Proyecto del Hackathon de Datos 2026 (ITM), modalidad Visualización.

## Mapa del repositorio

- `pipeline/`: Python. Extracción → normalización → consolidación → cruce → indicadores → publicación.
- `data/raw/`: descargas completas. **Fuera de git.** Puede contener datos personales.
- `data/snapshot/`: copia versionada, solo con columnas de la lista blanca y sin normalizar, más `manifest.json`.
- `data/outputs/`: salidas versionadas que consume el tablero. Es el contrato entre `pipeline/` y `web/`.
- `data/schema/`: JSON Schema del contrato, generado desde los modelos de Pydantic.
- `web/`: sitio Astro. Solo presenta lo que hay en `data/outputs/`.
- `docs/`: diseño, reglas y decisiones. Empieza por `docs/README.md`.
- `instrucciones.txt`: lo que sigue el jurado. Es un requisito habilitante del concurso.

## Comandos

| Tarea | mise | Equivalente nativo |
|---|---|---|
| Correr el pipeline desde la copia | `mise run pipeline` | `cd pipeline && uv run veeduria run --from-snapshot` |
| Actualizar desde las fuentes | `mise run refresh` | `cd pipeline && uv run veeduria run --refresh` |
| Regenerar el contrato | `mise run contract` | `cd pipeline && uv run veeduria export-schema`, luego `cd web && pnpm gen:types` |
| Servidor de desarrollo del sitio | `mise run dev` | `cd web && pnpm dev` |
| Construir y previsualizar el sitio | `mise run build` · `mise run preview` | `cd web && pnpm build` · `pnpm preview` |
| Todas las verificaciones | `mise run check` | Ver la lista de abajo |

mise es opcional. Todo debe seguir funcionando con los comandos nativos de `instrucciones.txt`, sin mise. Las tareas de mise solo llaman a `uv run` o `pnpm`; si una tarea necesita lógica, esa lógica va en el pipeline o en un script de `package.json`.

`mise run check` y la integración continua verifican, en este orden:

1. `ruff check` y `ruff format --check` en `pipeline/`.
2. `pytest` en `pipeline/`, sin las pruebas marcadas `network`.
3. Que el contrato regenerado no produzca cambios en `git diff` (`docs/adr/0004-contrato-pydantic-json-schema-ts.md`).
4. Que `pipeline/requirements.txt` coincida con `uv.lock` (`docs/adr/0013-python-con-uv-para-el-pipeline.md`).
5. Que la versión de pnpm sea la misma en `web/package.json`, `mise.toml` e `instrucciones.txt` (`docs/adr/0003-pnpm-sin-corepack.md`).
6. `astro check` y `pnpm build` en `web/`.

## Convención de idioma

- **Documentación, comentarios, docstrings, mensajes de log y textos del tablero:** español.
- **Código:** inglés. Nombres de módulos, funciones, variables, tablas, columnas derivadas, campos del contrato, ramas y flags de la CLI.
- Las columnas que vienen de las fuentes conservan su nombre original (`referencia_del_contrato`, `nombre_entidad`) hasta la normalización, donde se renombran según el glosario.

## Glosario del dominio

Usa siempre estos nombres en el código. Si necesitas un término nuevo, agrégalo aquí antes de usarlo.

| Español | Código |
|---|---|
| contrato | `contract` |
| proceso de contratación | `procurement_process` |
| secretaría (dependencia) | `department` |
| proveedor | `supplier` |
| persona jurídica / natural | `legal_entity` / `natural_person` |
| adición | `addition` |
| modalidad de contratación | `procurement_method` |
| contratación directa | `direct_award` |
| régimen especial | `special_regime` |
| causal o justificación de la modalidad | `method_justification` |
| oferente único | `single_bidder` |
| fecha de firma | `signed_date` |
| fecha de corte | `cutoff_date` |
| restricción de la Ley de Garantías | `electoral_restriction` |
| ventana de comparación | `comparison_window` |
| año de tratamiento / control | `treatment` / `control` |
| concentración pre-restricción | `pre_restriction_share` |
| Plan Anual de Adquisiciones | `procurement_plan` |
| copia de datos | `snapshot` |
| supresión de celdas pequeñas | `small_cell_suppression` |
| numerador / denominador / n | `numerator` / `denominator` / `sample_size` |

## Reglas no negociables

1. **Privacidad.** `data/raw/` está en `.gitignore` desde el primer commit, antes de descargar cualquier dato. Ninguna columna entra a `data/snapshot/` ni a `data/outputs/` si no está en `pipeline/sources.toml`. Nunca agregues a la lista blanca datos de personas naturales, funcionarios, supervisores ni cuentas bancarias. Nunca escribas datos personales en logs, fixtures ni mensajes de error.
2. **El dominio vive en Python.** `web/` no calcula, no filtra por reglas de negocio ni aplica supresión. Si una cifra aparece en el tablero, sale tal cual de `data/outputs/`.
3. **Determinismo.** Con la misma copia, el pipeline produce exactamente la misma salida. La fecha de corte sale de los datos, nunca del reloj. Ordena siempre antes de escribir.
4. **Trazabilidad.** Cada regla de negocio cita su identificador (R1–R17) y cada indicador el suyo (I1–I8), según `docs/reglas.md` y `docs/indicadores.md`, en el nombre del archivo, de la prueba o en un comentario.
5. **Lenguaje.** Ningún texto del proyecto habla de «corrupción», «irregular» o «sospechoso». Los indicadores son señales para revisar, no veredictos. Ver la guía de lenguaje en `docs/producto.md`.

## Documentación

Lee solo lo que la tarea necesita:

- `docs/reglas.md`: conceptos del dominio, catálogos y reglas R1–R17. Léelo antes de tocar normalización, consolidación o cruce.
- `docs/fuentes.md`: conjuntos de datos, llaves de cruce, lista blanca y problemas de calidad. Léelo antes de tocar la extracción.
- `docs/indicadores.md`: fórmulas de I1–I8 y metodología del hallazgo titular.
- `docs/producto.md`: propósito, alcance, tablero, ética y guía de lenguaje.
- `docs/plan.md`: cronograma, prioridades, riesgos y entregables.
- `docs/bitacora.md`: observaciones de la exploración de datos, con fechas y cifras.
- `docs/adr/`: un ADR por decisión técnica. Antes de proponer cambiar una herramienta o un enfoque, revisa si ya hay un ADR que explique por qué es así.

## Al trabajar

- Si tomas una decisión de diseño nueva, crea un ADR en `docs/adr/` con el siguiente número.
- Si cambias una regla, un indicador o una decisión, actualiza su documento en el mismo commit.
- Si algo en los datos contradice la documentación, detente y repórtalo; no ajustes la regla en silencio.
- El 8 de noviembre de 2026 a las 6:00 p. m. el proyecto se congela: desde ese momento solo se corrigen errores, no se agregan funciones.