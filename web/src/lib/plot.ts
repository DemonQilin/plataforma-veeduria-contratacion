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
  svg.setAttributeNS('http://www.w3.org/2000/xmlns/', 'xmlns', 'http://www.w3.org/2000/svg');
  return svg.outerHTML;
}
