# 0052. Tarjetas de la portada como tablas con barras CSS

- **Estado:** Aceptada
- **Fecha:** 2026-11-08
- **Fuente:** [0048](0048-decisiones-visuales-de-la-historia.md) y `odd/tasks/story-screens-1-5.md` (T4, S5, S6, S7)

## Contexto

La portada (pantalla 1) lleva cinco tarjetas de hallazgo con una mini gráfica cada una. Las figuras completas, con su CSV, viven en las pantallas 2 a 5 (ADR 0048, 0050).

## Decisión

- Cada mini gráfica es una `<table>` semántica con la barra dibujada en CSS (`aria-hidden`). La tabla es a la vez la gráfica y sus datos, así que cumple S5 sin `<details>`, CSV ni SVG propios. El `caption` (oculto a la vista) es la descripción en texto.
- Las cifras son las celdas de `data/outputs/` tal cual, formateadas con `format.ts`. El ancho de la barra es una escala visual y no se publica como cifra.
- Las frases con mínimo y máximo (años de comparación de I2 base y de «resto de tipos de contrato») salen de `i2Extremes`, que ordena y toma la celda; no calcula (S6).
- La frase «el conteo mensual bajó a entre 0 y 19 contratos durante las restricciones» exigiría filtrar meses por las fechas de la restricción, que es lógica de negocio: queda como marcador `[Texto pendiente …]` hasta que el pipeline o el compañero la den.
- El titular sigue siendo un borrador para el compañero (S8, L9).

## Consecuencias

- La portada no envía JavaScript.
- Las mini gráficas pueden diferir en forma de las figuras de sus pantallas, pero no en contenido.

## Alternativas

- **SVG de Plot por tarjeta:** descartada; añade DOM y peso a una vista de resumen, y la figura completa ya existe en su pantalla.
- **Calcular el rango mensual en `web/`:** descartada por la regla 2 de `CLAUDE.md`.
