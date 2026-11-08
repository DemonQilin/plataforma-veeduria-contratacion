// Fuente única de cada figura: el componente (SVG y tabla) y el CSV la leen,
// así que tabla y CSV no pueden diferir (docs/adr/0048).
import type { PlotOptions } from '@observablehq/plot';
import * as Plot from '@observablehq/plot';
import { directAwardMonthly } from './selectors';

export type Cell = string | number | null;

export interface FigureColumn {
  key: string;
  label: string;
  kind: 'text' | 'number';
  /** El valor sale vacío y se escribe «datos insuficientes» cuando la fila está suprimida. */
  suppressible?: boolean;
}

export interface FigureRow {
  values: Record<string, Cell>;
  suppressed: boolean;
}

export interface FigureSpec {
  id: string;
  title: string;
  /** Descripción en texto del gráfico (figcaption). */
  description: string;
  columns: readonly FigureColumn[];
  /** Clave de la columna con el n que se muestra junto a una celda suprimida. */
  sampleKey: string;
  rows: readonly FigureRow[];
  /** Si es true se generan un SVG de celular y otro de escritorio. */
  responsive?: boolean;
  plot: (size: 'small' | 'large') => PlotOptions;
}

const directMonthlyRows = directAwardMonthly();

export const FIGURES: readonly FigureSpec[] = [
  {
    id: 'contratacion-directa-por-mes',
    title: 'Contratos de contratación directa por mes',
    description: '[Texto pendiente: descripción de la figura (T6).]',
    columns: [
      { key: 'period', label: 'Mes', kind: 'text' },
      { key: 'contract_count', label: 'Contratos', kind: 'number' },
      { key: 'value', label: 'Valor (COP)', kind: 'number', suppressible: true },
    ],
    sampleKey: 'value_sample_size',
    rows: directMonthlyRows.map((row) => ({
      suppressed: row.is_suppressed,
      values: {
        period: row.period,
        contract_count: row.contract_count,
        value: row.value,
        value_sample_size: row.value_sample_size,
      },
    })),
    plot: (size) => ({
      width: size === 'small' ? 360 : 960,
      height: size === 'small' ? 260 : 360,
      x: {
        type: 'band',
        label: null,
        ticks: directMonthlyRows.map((row) => row.period).filter((p) => p.endsWith('-01')),
        tickFormat: (p: string) => p.slice(0, 4),
      },
      y: { label: 'Contratos', grid: true },
      marks: [
        Plot.barY(directMonthlyRows, {
          x: 'period',
          y: 'contract_count',
          fill: 'var(--chart-treatment)',
        }),
        Plot.ruleY([0]),
      ],
    }),
  },
];

export const getFigure = (id: string): FigureSpec => {
  const figure = FIGURES.find((candidate) => candidate.id === id);
  if (!figure) throw new Error(`Figura desconocida: ${id}`);
  return figure;
};
