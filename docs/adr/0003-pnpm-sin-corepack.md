# 0003. pnpm sin corepack

- **Estado:** Aceptada
- **Fecha:** 2026-10-29
- **Fuente:** [docs/plan.md](../plan.md#92-borrador-de-instruccionestxt)

## Contexto

El equipo prefiere pnpm para el tablero. A diferencia de npm, pnpm no viene con Node, así que el jurado necesita una forma de obtener la versión correcta.

El camino habitual era corepack, que lee el campo `packageManager` de `package.json` e instala esa versión. Pero desde Node.js 25 corepack ya no se distribuye con Node y hay que instalarlo aparte ([OpenReplay](https://blog.openreplay.com/manage-package-managers-node-corepack/)). Si el jurado descarga la versión actual de Node, `corepack enable` puede fallar con «comando no encontrado».

Las ventajas clásicas de pnpm (velocidad e instalación compartida en disco) casi no pesan en un proyecto de este tamaño. Lo que sí pesa es su `node_modules` estricto: una dependencia no declarada falla en la máquina del equipo, no en la del jurado.

## Decisión

- pnpm es el gestor de paquetes de `web/`. Su versión exacta se declara en el campo `packageManager` de `package.json`.
- El único lockfile es `pnpm-lock.yaml`. No se generan `package-lock.json` ni `yarn.lock`.
- Ningún camino depende de corepack:
  - **Opción A de `instrucciones.txt`:** `npx --yes pnpm@<versión> …`, que usa npm (incluido con Node) para ejecutar la versión exacta sin instalación global ni permisos de administrador.
  - **Opción B:** pnpm fijado en `mise.toml` (ver [0002](0002-mise-opcional-camino-nativo-primero.md)).
  - **Integración continua:** `pnpm/action-setup`, que lee el campo `packageManager`.
- Las instalaciones del jurado y de la integración continua usan `--frozen-lockfile`.

## Consecuencias

- Los comandos de la opción A son más largos (`npx --yes pnpm@10.x.y build` en vez de `npm run build`), pero no agregan ninguna instalación.
- La versión de pnpm aparece en tres lugares: `packageManager`, `mise.toml` e `instrucciones.txt`. Se cambian juntos, y `mise run check` verifica que coincidan.
- Una dependencia usada pero no declarada rompe el build en desarrollo, antes de llegar al jurado.
- pnpm usa *junctions* en Windows, que no requieren permisos de administrador.

## Alternativas

| Criterio | pnpm con `npx` (elegida) | pnpm con corepack | npm |
|---|---|---|---|
| Instalación extra para el jurado | Ninguna | corepack desde Node 25 | Ninguna |
| Versión exacta del gestor | Sí | Sí | La que trae su versión de Node |
| `node_modules` estricto | Sí | Sí | No: permite dependencias fantasma |
| Comandos en `instrucciones.txt` | Largos | Cortos | Cortos |

- **npm:** descartada por preferencia del equipo y por su `node_modules` plano, que permite usar dependencias no declaradas.
- **pnpm con corepack:** descartada porque corepack ya no viene con Node desde la versión 25.
- **`npm install -g pnpm`:** descartada porque una instalación global puede requerir permisos de administrador y deja una versión distinta en el sistema del jurado.
- **Yarn:** no se evaluó; no había preferencia por él y comparte el problema de corepack.