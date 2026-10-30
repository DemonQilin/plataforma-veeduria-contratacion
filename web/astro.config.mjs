import react from '@astrojs/react';
import { defineConfig } from 'astro/config';

// GitHub Pages: el sitio vive bajo /<repo>/ (docs/adr/0012).
export default defineConfig({
  site: 'https://demonqilin.github.io',
  base: '/plataforma-veeduria-contratacion/',
  integrations: [react()],
  vite: {
    server: {
      // El servidor de desarrollo lee ../data/outputs (docs/adr/0001).
      fs: { allow: ['..'] },
    },
  },
});