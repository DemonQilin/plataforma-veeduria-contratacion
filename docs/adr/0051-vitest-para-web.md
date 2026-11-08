# 0051. Vitest para probar los selectores de `web/`

- **Estado:** Aceptada
- **Fecha:** 2026-11-08
- **Fuente:** [0012](0012-astro-para-el-tablero.md), [0048](0048-decisiones-visuales-de-la-historia.md) y `odd/tasks/story-screens-1-5.md` (T3, S6)

## Contexto

`web/` no tenía corredor de pruebas. T3 crea los selectores que eligen celdas de `data/outputs/` para las pantallas 1 a 5, y la regla 2 de `CLAUDE.md` exige que no calculen ni filtren por reglas de negocio. Sin prueba, nada atrapa un selector que mezcle variantes o niveles.

## Decisión

- **Vitest** como dependencia de desarrollo de `web/`, con `pnpm test` (`vitest run`).
- `web/vitest.config.ts` usa `getViteConfig` de Astro, para que `import.meta.glob` de `src/lib/data.ts` funcione igual que en el sitio.
- Cada selector recibe los datos por parámetro, con las salidas reales por defecto; las pruebas pasan datos de ejemplo con celdas que no deben elegirse.
- `mise run check` y la integración continua suman el paso `pnpm test`, después de `astro check`.

## Consecuencias

- Una dependencia de desarrollo más; el sitio publicado no cambia.
- Las pruebas de `web/` se escriben junto al módulo (`*.test.ts`).

## Alternativas

- **`node --test` sin dependencias:** exigía separar los selectores de `data.ts` por el `import.meta.glob`. Se descarta.
- **Sin prueba automática:** como en T1 y T2; no deja nada que atrape una regresión.
