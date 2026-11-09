# 0054. Script mínimo para marcar la pantalla activa en el índice

- **Estado:** Aceptada
- **Fecha:** 2026-11-09
- **Fuente:** revisión visual del tablero del 9 nov 2026

## Contexto

En escritorio el índice lateral no indica en qué pantalla está el lector. La historia no cargaba JavaScript salvo el explorador (ADR 0012, 0050).

## Decisión

- Un `<script>` de unas 25 líneas en `Base.astro` usa `IntersectionObserver` y pone `aria-current="location"` en el enlace de la pantalla visible. El estilo vive en `global.css` y solo aplica desde 960 px.
- Es mejora progresiva: sin JavaScript el índice funciona igual que antes. El script no toca datos ni cifras.

## Consecuencias

- Excepción acotada a la regla «sin JavaScript en la historia»; `web/CLAUDE.md` y `web/AGENTS.md` la mencionan.

## Alternativas

- **CSS `scroll-target-group` y `:target-current`:** descartada; hoy solo funciona en Chrome reciente.
- **Sin resaltado:** descartada; el lector pierde la referencia en un recorrido largo.
