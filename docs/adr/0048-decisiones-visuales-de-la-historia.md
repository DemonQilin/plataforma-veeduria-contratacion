# 0048. Decisiones visuales de la historia guiada (pantallas 1 a 5)

- **Estado:** Aceptada
- **Fecha:** 2026-11-08
- **Fuente:** [docs/producto.md](../producto.md#32-recorrido-de-la-historia-guiada) (pantallas 1 a 5), [docs/plan.md](../plan.md#7-riesgos-y-planes-b) (plan B de Astro) y `odd/tasks/story-screens-1-5.md` (S4, L8, L10 a L13)

## Contexto

Las maquetas de las pantallas 1 a 5 se aprobaron el 8 nov con la propuesta B (referentes: Stack Overflow Developer Survey 2025 y State of JS 2025). Antes de escribir el sitio hay que fijar qué se decidió en lo visual y resolver dos choques con [0012](0012-astro-para-el-tablero.md): los botones «Por número | Por valor | Sin interadministrativos» de la pantalla 4 parecen pedir JavaScript, y «Descargar datos» pide archivos que hoy no existen en el sitio.

Al 6 nov no había avance en Astro, así que aplica el plan B de `plan.md`: una sola página estática sin islas. Este ADR complementa a 0012 y no toca el explorador (pantalla 6).

## Decisión

- **Una sola página** (`web/src/pages/index.astro`) con un ancla por pantalla. En escritorio lleva un índice lateral con las 9 pantallas y enlaces anterior/siguiente; en celular, solo anterior/siguiente.
- **Cero JavaScript en las pantallas 1 a 5.** Los gráficos son SVG de Observable Plot generados en el build (0012). Donde la orientación cambia entre celular y escritorio (barras de la pantalla 4, línea de tiempo de la 2), se generan dos SVG y una media query muestra uno.
- **Selector de la pantalla 4 sin JavaScript.** Se generan tres SVG y tres tablas (por número, por valor, sin interadministrativos) y botones de radio con `:has()` muestran el elegido. Dentro de `@supports selector(:has(*))` se oculta lo no elegido; si el navegador no soporta `:has()`, se ven los tres apilados, con el mismo contenido.
- **Paleta «Pizarra y naranja»**, en claro y oscuro con `prefers-color-scheme`, que reemplaza los colores de D1; la tipografía (Atkinson Hyperlegible Next), los 4 espacios y los 3 radios de D1 se mantienen.

  | Token | Claro | Oscuro |
  |---|---|---|
  | `surface` | #f4f6f9 | #0b1120 |
  | `raised` | #ffffff | #131c2e |
  | `ink` | #0f172a | #f1f5f9 |
  | `muted` | #475569 | #a3b0c2 |
  | `hair` | #7c8799 | #6b7a90 |
  | `accent` | #2563eb | #7cacf8 |
  | `on-accent` | #ffffff | #0b1120 |
  | `chart-treatment` (años con elecciones) | #ea580c | #fb923c |
  | `chart-control` (años de comparación) | #475569 | #7b8799 |
  | `chart-suppressed` | #334155 | #a3b0c2 |
  | `chart-grid` | #e2e8f0 | #1e293b |
  | `chart-restriction` (banda) | #ffedd5 | #3a2414 |

  El contraste se midió con WCAG: texto ≥ 4,5:1 y marcas, bordes y foco ≥ 3:1, sin fallos en ninguno de los dos temas. Elecciones frente a comparación se distinguen también por luminosidad (L* 57/36 en claro, 70/56 en oscuro), no solo por tono. No se usa coral ni rojo: se lee como alarma y contradice la guía de lenguaje de `producto.md`.
- **Restricción.** La de contratación directa va con relleno `chart-restriction`; en la línea de tiempo y en la tarjeta de la portada lleva además borde `chart-treatment` de 2 px, y en la pantalla 3 va sin borde, detrás de las barras. La de convenios interadministrativos va solo con borde discontinuo y sin relleno.
- **Celda suprimida.** Se escribe «datos insuficientes» junto a su n, en `chart-suppressed`. En la serie mensual solo se suprime el valor y el conteo se dibuja ([0040](0040-serie-mensual-con-valor-suprimido.md)), así que la celda suprimida se ve en la tabla de datos de la pantalla 3. Las cifras anuales del Distrito nunca se suprimen, por lo que las barras de la pantalla 4 no tienen huecos.
- **Cada figura** lleva su descripción en texto (`figcaption`), su tabla de datos en `<details>` y su CSV. «Copiar enlace» es un enlace normal al ancla de la figura, porque copiar al portapapeles necesitaría JavaScript.
- **CSV por gráfica**, generado en el build con un endpoint estático de Astro (`getStaticPaths`). Usa el mismo selector de celdas que la tabla, así que tabla y CSV no pueden diferir. Va en UTF-8 con BOM, separado por comas y con punto decimal; la celda suprimida sale con el valor vacío y una columna `suprimida`. No es cálculo: son las celdas que ya se ven (regla 2 de `CLAUDE.md`). Los archivos van bajo CC BY-SA 4.0 ([0015](0015-datos-y-textos-con-cc-by-sa.md)).
- **Forma.** Bordes de 2 px y ninguna sombra decorativa. En celular, la frase de la portada baja de `display` a `h2`.
- **Textos.** Son del compañero; hasta que lleguen van marcadores `[Texto pendiente …]`. Los titulares de las tarjetas de la portada son un borrador.

## Consecuencias

- Las pantallas 1 a 5 no envían JavaScript y se ven aunque el script falle.
- La página trae los tres SVG de la pantalla 4 y los SVG por tamaño de pantalla de la 2 y la 4, aunque solo se vea uno: unos pocos KB más.
- La tarea T2 queda obligada a generar los CSV y a elegir el DOM para Plot en el servidor (pendiente en 0012).
- El artefacto de D1 en Claude Design se actualizó con esta paleta el 8 nov; si difieren, manda este ADR para el sitio.
- Sigue abierta la discrepancia entre `docs/indicadores.md` y `indicators.json` (L7); se corrige en un commit aparte cuando se decida qué cifra manda.

## Alternativas

- **Isla de React para el selector de la pantalla 4:** descartada. Rompe «sin islas» del plan B y sube el JavaScript de una pantalla que no lo necesita.
- **Enlazar el JSON de `data/outputs/` en GitHub, o copiar los JSON al sitio:** descartadas. Entregan el archivo completo en JSON en vez de lo que muestra la gráfica; se eligió el CSV por gráfica.
- **Copiar el enlace con JavaScript:** descartada por la misma razón que la isla.
- **Paletas 2 y 3 de la comparación del 8 nov:** descartadas; se eligió la 1.
