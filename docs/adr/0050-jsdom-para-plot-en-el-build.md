# 0050. jsdom como DOM de Observable Plot en el build

- **Estado:** Aceptada
- **Fecha:** 2026-11-08
- **Fuente:** [0012](0012-astro-para-el-tablero.md) (DOM de Plot pendiente), [0048](0048-decisiones-visuales-de-la-historia.md) y `odd/tasks/story-screens-1-5.md` (T2, S4 y S5)

## Contexto

El ADR 0012 deja a Observable Plot generando SVG en el build, sin JavaScript en el navegador, pero no decide qué librería le da el DOM en el servidor. La tarea T2 necesita decidirlo para construir `Figure` y el CSV por gráfica de [0048](0048-decisiones-visuales-de-la-historia.md).

## Decisión

- **jsdom** en `web/` (`jsdom` y `@types/jsdom`). Se crea un documento una vez y se pasa a Plot con la opción `document`; el SVG se serializa con `outerHTML`, como en la guía de Plot para Node.
- La función `renderPlot` (`web/src/lib/plot.ts`) es el único lugar que importa jsdom. Solo corre en el build: el navegador no recibe la librería.
- Los colores de las marcas son `var(--chart-*)`, así que el tema oscuro cambia sin JavaScript.
- Cada figura se declara una vez en `web/src/lib/figures.ts` (descripción, columnas, filas y gráfico). El componente `Figure` y el CSV leen esa misma declaración, por lo que tabla y CSV no pueden diferir.

## Consecuencias

- Más paquetes en `devDependencies` y un `pnpm install` más largo; el sitio publicado no cambia de tamaño.
- Si Plot cambia la forma de serializar, solo se toca `plot.ts`.

## Alternativas

- **linkedom:** más liviana y rápida, pero la guía oficial de Plot usa jsdom; con linkedom el soporte de cualquier fallo sería nuestro. Se descarta por ahora.
