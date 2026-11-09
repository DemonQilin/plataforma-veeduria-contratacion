// Observable Plot en el build: jsdom pone el DOM y el resultado es una cadena SVG
// que el navegador recibe sin JavaScript (docs/adr/0048, docs/adr/0050).
import * as Plot from '@observablehq/plot';
import { JSDOM } from 'jsdom';

const document = new JSDOM('').window.document;

export function renderPlot(options: Plot.PlotOptions): string {
  const svg = Plot.plot({
    style: { fontSize: '14px', fontFamily: 'inherit', background: 'transparent' },
    ...options,
    document,
  });
  // Plot rotula cada grupo de marcas con aria-label, pero un <g> sin rol no admite ese atributo
  // (axe: aria-prohibited-attr). La descripción y la tabla de datos ya dicen lo que muestra el gráfico.
  for (const group of svg.querySelectorAll('g[aria-label]:not([role])')) {
    group.removeAttribute('aria-label');
  }
  svg.setAttributeNS('http://www.w3.org/2000/xmlns/', 'xmlns', 'http://www.w3.org/2000/svg');
  return svg.outerHTML;
}
