# 0053. Explorador como isla de React y etiquetas de secretaría en `web/`

- **Estado:** Aceptada
- **Fecha:** 2026-11-09
- **Fuente:** [0012](0012-astro-para-el-tablero.md), [0048](0048-decisiones-visuales-de-la-historia.md) y `docs/producto.md` §3.3

## Contexto

La pantalla 6 es el explorador de I1, I3, I4 e I5 por año y secretaría. El plan B (ADR 0048) dejó la historia sin islas, pero el explorador necesita elegir indicador, año y secretaría en el navegador. Además, `indicators.json` trae solo el código de la secretaría, sin su nombre.

## Decisión

- El explorador es una isla de React (`Explorer.tsx`) con `client:visible`. El resto de la página sigue sin JavaScript.
- `lib/explorer.ts` elige, ordena y da formato a las cifras en el build; la isla solo las muestra. No calcula (regla 2 de `CLAUDE.md`). Los selectores se apoyan en `explorerCells`: variante base y la medida con que se publica cada indicador (I4 solo por valor).
- El ancho de cada barra es `ratio × 72`, una escala visual igual a la de las tarjetas de la portada (ADR 0052). No es una cifra publicada y la cifra que se lee sale tal cual de la celda. La excepción es solo de dibujo.
- Las celdas suprimidas (R13) llegan marcadas: se muestran como «datos insuficientes» con su n y van al final del ranking.
- Las etiquetas de secretaría se copian de `pipeline/reference/departments.toml` a `lib/departments.ts`. Una prueba verifica que cada código de `indicators.json` tenga etiqueta.

## Consecuencias

- La pantalla 6 envía el runtime de React; las demás pantallas no.
- Si el catálogo de secretarías cambia, hay que actualizar `departments.ts` (la prueba avisa si falta un código).

## Alternativas

- **Selector sin JavaScript (`:has()`, como la pantalla 4):** descartada; generaría CSS por cada combinación y un detalle por secretaría más débil.
- **Agregar `label` al contrato de Pydantic:** descartada por tiempo (congelamiento del 9 nov); sería lo más limpio a futuro.
