/// <reference types="vitest/config" />
import { getViteConfig } from 'astro/config';

// Reusa la configuración de Vite de Astro para que `import.meta.glob` de
// `src/lib/data.ts` funcione igual en las pruebas (docs/adr/0051).
export default getViteConfig({
  test: { include: ['src/**/*.test.ts'] },
});
