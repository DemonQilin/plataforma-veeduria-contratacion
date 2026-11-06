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
| D1 | S1, S2 | Sistema de diseño en Claude Design | en línea | hecho (aprobado por Juan) | https://claude.ai/artifact/6snvHytHXX7jgJrvGnW5Cj; contraste 0 fallos de 34 pares (claro y oscuro) |
| D2 | S1, S3, S7 | Maquetas de las pantallas 1 a 5 | en línea | publicado, en revisión de Juan | https://claude.ai/artifact/7N3pGHDvcUtof3SHWEUQUv; 10 mesas (5 pantallas × celular 390 px y escritorio 1440 px); cifras comparadas con `data/outputs/`: 0 diferencias; sin renderizar en navegador |
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
- **L3 (6 nov 2026).** D1 publicado: 14 tokens de color en claro y oscuro, texto en Atkinson Hyperlegible Next, 4 espacios, 3 radios, README y portada. Medido con WCAG: 17 pares por tema, 0 fallos (texto ≥ 4,5:1; marcas, bordes y foco ≥ 3:1). `validate_palette.js` sobre tratamiento y control: separación normal ΔE 17,8 (claro) y 16,3 (oscuro), CVD ΔE 14,4 y 9,0, contraste ≥ 3:1. El validador marca el piso de croma del gris del control: es neutro a propósito y queda anotado en el README. Falta que Juan lo revise en el navegador antes de D2.
- **L4 (6 nov 2026).** Juan aprobó D1: «Aprobado, guarda que ya lo hicimos y todavía no empieces D2». Siguiente: D2, a la espera de su señal.
- **L5 (6 nov 2026).** Juan aprobó el plan de D2 («Aprobado. Espera mi señal antes de iniciar») y después dio la señal: «Procede». D2 publicado en https://claude.ai/artifact/7N3pGHDvcUtof3SHWEUQUv con el sistema de D1 instalado: 10 mesas (portada, la regla, el patrón, la comparación y la objeción, cada una en celular y escritorio; la 3 de escritorio en tema oscuro). Las cifras salen de `data/outputs/` y se compararon con un script: 0 diferencias en I2 (base, `service_contract`, `non_service_contract`, `spans_restriction`) ni en la serie mensual. No se renderizó en un navegador (el lienzo es privado y no hay sesión); Juan lo revisa. Textos del compañero como marcadores `[Texto pendiente …]` (S8).
- **L6 (6 nov 2026).** Supuesto confirmado: la duración de los contratos de enero (pantalla 5) se lee con `spans_restriction`; sale 99,6 / 55,2 / 69,9 / 98,9 / 99,2 % y se rotula «no concluyente», como en `docs/indicadores.md`.
- **L7 (6 nov 2026).** Los datos contradicen la documentación en dos cifras, y no se ajustó la regla en silencio: (a) `docs/indicadores.md` (líneas 98 y 115) da 29,8 % para el mejor año de control de I2 por valor y una brecha de 0,9 puntos; `indicators.json` da 28,9 % (2023) y 1,8 puntos; (b) la línea 66 da 99,0 % (701 de 708) para `spans_restriction` de 2026; `indicators.json` da 99,2 % (701 de 707). Las maquetas usan `data/outputs/`. Pendiente: confirmar con Juan cuál manda y corregir el documento en un commit aparte.
- **L8 (6 nov 2026).** Decisiones visuales nuevas que D3 debe recoger y Juan debe aprobar con las maquetas: (1) la restricción de contratación directa va con relleno `chart-restriction`; la de convenios interadministrativos, solo con borde discontinuo y sin relleno; (2) en celular, las barras de la pantalla 4 pasan de verticales a horizontales y la línea de tiempo de la 2 pasa de horizontal a vertical, y la frase de la portada baja de `display` a `h2`; (3) la celda suprimida se ve en la tabla de datos de la pantalla 3 (valor mensual con `datos insuficientes`), porque en la serie mensual solo se suprime el valor (ADR 0040), no el conteo.
