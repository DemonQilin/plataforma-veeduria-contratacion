import react from '@astrojs/react';
import { defineConfig, fontProviders } from 'astro/config';

// GitHub Pages: el sitio vive bajo /<repo>/ (docs/adr/0012).
export default defineConfig({
  site: 'https://demonqilin.github.io',
  base: '/plataforma-veeduria-contratacion/',
  integrations: [react()],
  // Se descarga en el build y se sirve desde el propio sitio (docs/adr/0048).
  fonts: [
    {
      provider: fontProviders.google(),
      name: 'Atkinson Hyperlegible Next',
      cssVariable: '--font-sans',
      weights: [400, 700],
      styles: ['normal'],
      subsets: ['latin'],
      fallbacks: ['system-ui', 'sans-serif'],
    },
  ],
  vite: {
    server: {
      // El servidor de desarrollo lee ../data/outputs (docs/adr/0001).
      fs: { allow: ['..'] },
    },
  },
});