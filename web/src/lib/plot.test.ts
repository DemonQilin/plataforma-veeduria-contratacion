// T10 (S5): el SVG de Plot no debe llevar atributos ARIA prohibidos (axe: aria-prohibited-attr).
import * as Plot from '@observablehq/plot';
import { describe, expect, it } from 'vitest';
import { renderPlot } from './plot';

describe('renderPlot', () => {
  const svg = renderPlot({
    width: 300,
    height: 120,
    marks: [Plot.barY([{ x: 'a', y: 1 }], { x: 'x', y: 'y' }), Plot.ruleY([0])],
  });

  it('no deja aria-label en ningún grupo sin rol', () => {
    expect(svg).not.toMatch(/<g[^>]* aria-label=|<g aria-label=/);
  });
});
