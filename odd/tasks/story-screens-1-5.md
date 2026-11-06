# Pantallas 1 a 5 de la historia guiada

Objetivo: el bloque del 5 al 6 nov de `docs/plan.md:38`, con una fase de diseño en Claude Design antes de escribir el sitio. Rama: `feat/story-screens-1-5`. Entrega: `ask-on-risk`. Verificación: `mise run check` (`astro check`, `pnpm build`) y revisión en el navegador.

## Specs

- **S1.** «Define la lista de tareas para este objetivo, incluye una fase de diseño (con claude design) y muestra pera revisar». La fase de diseño se hace en Claude Design, antes de escribir código, con un tope de 1,5 h.
- **S2.** Sistema de diseño con colores en claro y oscuro, tipografía y espacios, más una paleta de gráficos para años con elecciones, años de comparación, sombreado de la restricción y celda suprimida, con contraste accesible.
- **S3.** Maquetas de las pantallas 1 a 5 (`docs/producto.md:102`) en celular y escritorio, con las cifras reales de `data/outputs/`. Las aprueba Juan antes de implementar.
- **S4.** Un ADR con las decisiones visuales: una sola página, gráficos SVG en el build sin islas (plan B de `docs/plan.md:120`), paleta y cómo se ve una celda suprimida.
- **S5.** Cada gráfico lleva su descripción en texto y su tabla de datos (`docs/producto.md:97`).
- **S6.** `web/` no calcula ni filtra por reglas de negocio: solo elige celdas de `data/outputs/` (regla 2 de `CLAUDE.md`).
- **S7.** Pantallas: (1) portada con el titular de I2 base por número de contratos y la fecha de corte; (2) línea de tiempo de la Ley de Garantías de 2022 a 2027; (3) contratación directa por mes con la restricción sombreada; (4) barras de I2 por año, con elecciones frente a comparación; (5) prestación de servicios frente al resto y contratos de enero que terminan después de la restricción.
- **S8.** Los textos son del compañero; mientras no lleguen van marcadores de posición. Ningún texto habla de «corrupción», «irregular» o «sospechoso».
- **S9.** El punto de decisión 2 (vie 6 nov) queda anotado en `docs/plan.md` y en `docs/bitacora.md`.
- *Supuesto:* la duración de los contratos de enero de la pantalla 5 se lee con la variante `spans_restriction` de I2. Se confirma en D2.

## Tareas

| ID | Specs | Tarea | Ruta | Estado | Evidencia |
|---|---|---|---|---|---|
| D1 | S1, S2 | Sistema de diseño en Claude Design | en línea | pendiente | |
| D2 | S1, S3, S7 | Maquetas de las pantallas 1 a 5 | en línea | pendiente | |
| D3 | S4 | ADR de decisiones visuales | en línea | pendiente | |
| T1 | S2, S4 | Colores en CSS, diseño general y recorrido en `Base.astro` | en línea | pendiente | |
| T2 | S4, S5 | Componente `Figure` y SVG de Observable Plot en el build | en línea | pendiente | |
| T3 | S6 | Selectores de celdas en `web/src/lib/` | en línea | pendiente | |
| T4 | S7 | Pantalla 1 · Portada | en línea | pendiente | |
| T5 | S7 | Pantalla 2 · La regla | en línea | pendiente | |
| T6 | S7 | Pantalla 3 · El patrón | en línea | pendiente | |
| T7 | S7 | Pantalla 4 · La comparación | en línea | pendiente | |
| T8 | S7 | Pantalla 5 · La objeción | en línea | pendiente | |
| T9 | S8 | Textos del compañero | en línea | pendiente | |
| T10 | S5 | Verificación: `mise run check`, celular y Lighthouse | en línea | pendiente | |
| T11 | S9 | Punto de decisión 2 | en línea | pendiente | |

Ruta: todo en línea; no hay unidades paralelas con superficies separadas que justifiquen un escritor delegado.

## Log

- **L1 (6 nov 2026).** «Define la lista de tareas para este objetivo, incluye una fase de diseño (con claude design) y muestra pera revisar». Juan aprobó la lista tal cual: «Apruebo».
- **L2 (6 nov 2026).** Las salidas cubren las 5 pantallas. El plan B de Astro (`docs/plan.md:120`) ya aplica porque al 6 nov no había avance en el sitio. Siguiente: D1.
