# 0012. Astro para el tablero, con islas de React

- **Estado:** Aceptada
- **Fecha:** 2026-10-29
- **Fuente:** [docs/producto.md](../producto.md#34-stack-y-despliegue)

## Contexto

El tablero es una historia guiada con datos para público no técnico, pensada primero para el celular. La mayor parte es contenido: textos, gráficos estáticos y una página por secretaría. Solo el explorador de indicadores necesita interacción en el navegador.

El sitio debe funcionar durante la evaluación sin un servidor que mantener, publicarse en GitHub Pages desde el mismo repositorio y cargar rápido en conexiones móviles. Los datos ya vienen calculados del pipeline (ver [0005](0005-dominio-solo-en-python.md)), así que el sitio no necesita backend.

El equipo domina React, pero no ha usado Astro.

## Decisión

- **Sitio estático generado con Astro**, con TypeScript estricto.
- **React solo en las islas interactivas:** el explorador de indicadores, hidratado con `client:visible`.
- **Gráficos con Observable Plot:** renderizados como SVG en el build para la historia, sin JavaScript en el navegador; en el navegador solo dentro del explorador.
- **Una página estática por secretaría**, generada con `getStaticPaths`, con su propia tarjeta al compartir.
- **Despliegue en GitHub Pages** con la acción oficial de Astro, desde GitHub Actions.

## Consecuencias

- Las páginas de la historia no envían JavaScript: cargan rápido en celulares y los gráficos se ven aunque el script falle.
- Los gráficos generados en el build son SVG accesibles, con descripción y tabla de datos.
- Observable Plot necesita un DOM para renderizar en el servidor; se le pasa con la opción `document`. La librería que lo provee se decide en un ADR aparte.
- El sitio vive bajo una ruta base en GitHub Pages: `site` y `base` deben configurarse, y todo enlace interno debe usar `import.meta.env.BASE_URL`.
- Aprender Astro cuesta un estimado de 4 horas. Plan B (ver [`plan.md`](../plan.md#7-riesgos-y-planes-b)): si al mediodía del 5 nov no hay avance, se hace una sola página estática sin islas y el explorador se simplifica.

## Alternativas

Comparación hecha en el diseño del MVP, antes de tomar la decisión.

| Criterio | Astro (elegida) | Next.js (exportación estática) |
|---|---|---|
| Para qué está pensado | Sitios de contenido, como esta historia con datos | Aplicaciones web |
| JavaScript enviado | Ninguno por defecto; solo en las islas interactivas | El runtime de React y la hidratación de toda la página |
| Gráficos estáticos | Naturales: se generan como SVG en el build | Posibles, pero hay que manejar la frontera servidor-cliente |
| Páginas por secretaría | `getStaticPaths` | `generateStaticParams` |
| GitHub Pages | Guía y acción oficiales | Requiere configurar ruta base, imágenes y barras finales |
| Curva de aprendizaje | Nueva, pero corta: sintaxis cercana a HTML, y React se reutiliza en las islas | Depende de la experiencia previa con el App Router |
| Valor en el mercado laboral | Menor reconocimiento | Mucho más pedido |
| Crecimiento futuro | Soporta servidor y API con adaptadores | Soporta servidor y API de forma nativa |

- **Next.js:** descartada. Gana en reconocimiento laboral y en crecimiento hacia una aplicación, pero ese valor pesa poco en un posicionamiento orientado a backend e infraestructura, y el proyecto es una historia con datos para leer en celulares, exactamente para lo que Astro está diseñado.
- **HTML estático escrito a mano o con un generador sin componentes:** no se evaluó a fondo; el explorador y las páginas por secretaría necesitan componentes y generación de rutas.

La elección es reversible a bajo costo: las islas son componentes de React que funcionarían igual en otro framework, y los datos llegan por `src/lib/data.ts`.