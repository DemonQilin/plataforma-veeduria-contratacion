# web/

Tablero ciudadano en Astro. Las convenciones generales (idioma, glosario, reglas no negociables) están en el `CLAUDE.md` de la raíz.

## Stack

- Astro con TypeScript. `tsconfig.json` extiende de `astro/tsconfigs/strictest`.
- React solo para las islas interactivas (el explorador de indicadores), en archivos `.tsx`.
- Observable Plot para los gráficos.
- pnpm, con la versión declarada en `packageManager` de `package.json`. No uses npm ni yarn para instalar, no generes otro lockfile y no dependas de corepack (ver `docs/adr/`).
- Node en la versión de `.node-version`.

## Acceso a los datos

- **Un solo punto de entrada:** `src/lib/data.ts` es el único archivo que importa desde `../data/outputs`. El resto del sitio usa las funciones que exporta.
- **Tipos generados:** `src/types/contract.ts` se genera con `mise run contract` desde `data/schema/`. Nunca lo edites a mano. Si un tipo no te sirve, el cambio va en los modelos de Pydantic del pipeline.
- `astro.config.mjs` incluye `..` en `vite.server.fs.allow` para que el servidor de desarrollo pueda leer `data/outputs/`.
- El sitio nunca consulta APIs externas, ni en el build ni en el navegador.

## Qué no hace el tablero

- No calcula ni recalcula indicadores, proporciones ni totales.
- No filtra por reglas de negocio ni aplica la supresión de celdas pequeñas: eso ya viene resuelto en `data/outputs/`. Las celdas suprimidas llegan marcadas y se muestran como «datos insuficientes».
- No muestra contratos individuales ni nombres de personas. Solo proveedores que son personas jurídicas, y solo en el indicador de concentración (I4).

Lo único que hace con los datos es darles formato y dibujarlos.

## Gráficos

- Los gráficos de la historia se renderizan como SVG en el build, sin JavaScript en el navegador. Observable Plot necesita un DOM en el servidor: se le pasa con la opción `document` (la librería exacta queda en un ADR).
- Solo el explorador renderiza en el navegador, como isla de React con `client:visible`.
- Cada gráfico lleva una frase que dice qué muestra, una descripción en texto y su tabla de datos accesible.

## Formato y textos

- Todos los textos visibles están en español, con lenguaje ciudadano y según la guía de lenguaje de `docs/producto.md`.
- Números y fechas con `Intl.NumberFormat` y `Intl.DateTimeFormat` en `es-CO`. Formatea en un solo módulo (`src/lib/format.ts`), no en cada componente.
- Toda cifra muestra su base: «52 % de 1.390 contratos», no un porcentaje suelto.
- Cada indicador muestra la fecha de corte y su n.

## Publicación en GitHub Pages

- El sitio vive bajo una ruta base (`/<repo>/`). `site` y `base` se configuran en `astro.config.mjs`.
- Todos los enlaces internos y recursos se construyen con `import.meta.env.BASE_URL`. Nunca escribas rutas absolutas como `/secretarias/...`.
- Durante el concurso, el sitio lleva `noindex` en todas las páginas y un `robots.txt` que bloquea la indexación.
- Etiquetas Open Graph en todas las páginas, incluidas las de cada secretaría.

## Diseño

- Primero el celular: diseña para pantallas angostas y amplía después.
- Las páginas de la historia no cargan JavaScript, salvo el explorador.

## Comandos

- `pnpm dev` · `pnpm build` · `pnpm preview`
- `pnpm astro check`: revisa los tipos, incluidos los archivos `.astro`. Debe pasar antes de cada commit.