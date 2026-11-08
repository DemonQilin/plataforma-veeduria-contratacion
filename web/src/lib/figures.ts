// Fuente única de cada figura: el componente (SVG y tabla) y el CSV la leen,
// así que tabla y CSV no pueden diferir (docs/adr/0048).
import type { PlotOptions } from '@observablehq/plot';
import * as Plot from '@observablehq/plot';
import { getMetadata } from './data';
import { formatDate } from './format';
import { directAwardMonthly, restrictions } from './selectors';

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
  sampleKey?: string;
  rows: readonly FigureRow[];
  /** Si es true se generan un SVG de celular y otro de escritorio. */
  responsive?: boolean;
  plot: (size: 'small' | 'large') => PlotOptions;
}

const directMonthlyRows = directAwardMonthly();

// Pantalla 2: periodos de la Ley de Garantías. Solo elige y da formato a las celdas de
// electoral_calendar.json; las posiciones y el «+1 día» (el último día se pinta completo)
// son escala visual, no cifras (S6).
const DAY = 86_400_000;
const scopeLabel = { direct_award: 'Contratación directa', interadministrative: 'Convenios interadministrativos' } as const;
const statusLabel = { ended: 'Terminada', ongoing: 'En curso', upcoming: 'Próxima' } as const;
const cutoff = getMetadata()?.cutoff_date;
const cutoffDate = cutoff ? new Date(`${cutoff}T00:00:00Z`) : undefined;
const timeline = restrictions().map((item) => {
  const start = Date.parse(`${item.start}T00:00:00Z`);
  const end = Date.parse(`${item.end}T00:00:00Z`) + DAY;
  return {
    item,
    direct: item.scope === 'direct_award',
    scope: scopeLabel[item.scope],
    status: statusLabel[item.status],
    start: new Date(start),
    end: new Date(end),
    middle: (start + end) / 2,
    label: `del ${formatDate(item.start)}\nal ${formatDate(item.end)}\n${statusLabel[item.status]}`,
  };
});
const timelineStart = new Date(Date.UTC(Number(timeline[0]?.item.start.slice(0, 4) ?? 2022), 0, 1));
const timelineEnd = new Date(Date.UTC(Number(timeline.at(-1)?.item.end.slice(0, 4) ?? 2027) + 1, 0, 1));
// Los años que marcan el eje (sin el 1 de enero que cierra la escala).
const yearStarts = Array.from(
  { length: timelineEnd.getUTCFullYear() - timelineStart.getUTCFullYear() },
  (_, index) => new Date(Date.UTC(timelineStart.getUTCFullYear() + index, 0, 1)),
);
// Contorno del color de la tarjeta para que la línea de corte no tache los rótulos.
const halo = { fill: 'currentColor', stroke: 'var(--surface-raised)', strokeWidth: 5 } as const;
const directRestrictions = timeline.filter((entry) => entry.direct);
const interadministrativeRestrictions = timeline.filter((entry) => !entry.direct);
const rangesOf = (direct: boolean) =>
  timeline
    .filter((entry) => entry.direct === direct)
    .map((entry) => `del ${formatDate(entry.item.start)} al ${formatDate(entry.item.end)}${entry.item.status === 'upcoming' ? ' (próxima)' : ''}`)
    .join('; ');
const restrictionStyle = {
  direct: { fill: 'var(--chart-restriction)', stroke: 'var(--chart-treatment)', strokeWidth: 2 },
  interadministrative: { fill: 'none', stroke: 'var(--chart-axis)', strokeWidth: 1.5, strokeDasharray: '5 4' },
} as const;
// En celular los rótulos van en una columna: se separan en el tiempo para que no se pisen.
const SMALL_HEIGHT = 700;
const labelGap = (64 / (SMALL_HEIGHT - 60)) * (timelineEnd.getTime() - timelineStart.getTime());
let previousLabel = Number.NEGATIVE_INFINITY;
const stackedLabels = timeline
  .toSorted((a, b) => a.middle - b.middle)
  .map((entry) => {
    previousLabel = Math.max(entry.middle, previousLabel + labelGap);
    return { ...entry, at: new Date(previousLabel) };
  });
const cutoffLabel = cutoff ? `Fecha de corte · ${formatDate(cutoff)}` : '';

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
  {
    id: 'periodos-de-restriccion',
    title: 'Periodos de restricción de la Ley de Garantías, de 2022 a 2027',
    description:
      `Línea de tiempo de ${timelineStart.getUTCFullYear()} a ${timelineEnd.getUTCFullYear() - 1} con ${timeline.length} periodos de restricción. ` +
      `Contratación directa: ${rangesOf(true)}. Convenios interadministrativos: ${rangesOf(false)}.` +
      (cutoff ? ` La fecha de corte de los datos es el ${formatDate(cutoff)}.` : ''),
    columns: [
      { key: 'scope', label: 'Alcance', kind: 'text' },
      { key: 'start', label: 'Inicio', kind: 'text' },
      { key: 'end', label: 'Fin', kind: 'text' },
      { key: 'status', label: 'Estado', kind: 'text' },
    ],
    responsive: true,
    rows: timeline.map((entry) => ({
      suppressed: false,
      values: {
        scope: entry.scope,
        start: formatDate(entry.item.start),
        end: formatDate(entry.item.end),
        status: entry.status,
      },
    })),
    plot: (size) =>
      size === 'large'
        ? {
            width: 960,
            height: 340,
            marginLeft: 250,
            marginRight: 70,
            marginTop: 36,
            x: { type: 'utc', domain: [timelineStart, timelineEnd], ticks: yearStarts, tickFormat: '%Y', axis: 'top', label: null, grid: true },
            y: { type: 'band', domain: [scopeLabel.direct_award, scopeLabel.interadministrative], label: null, padding: 0.55 },
            marks: [
              ...(cutoffDate ? [Plot.ruleX([cutoffDate], { stroke: 'var(--ink)', strokeWidth: 2, strokeDasharray: '6 4' })] : []),
              Plot.barX(directRestrictions, { x1: 'start', x2: 'end', y: 'scope', ...restrictionStyle.direct }),
              Plot.barX(interadministrativeRestrictions, { x1: 'start', x2: 'end', y: 'scope', ...restrictionStyle.interadministrative }),
              Plot.text(timeline, { x: (d) => new Date(d.middle), y: 'scope', text: 'label', dy: 34, lineAnchor: 'top', ...halo }),
              ...(cutoffDate
                ? [
                    Plot.text([cutoffDate], { x: (d: Date) => d, text: () => cutoffLabel, frameAnchor: 'top', textAnchor: 'end', lineAnchor: 'top', dx: -6, dy: 4, fontWeight: 700 }),
                  ]
                : []),
            ],
          }
        : {
            width: 360,
            height: SMALL_HEIGHT,
            marginLeft: 44,
            marginRight: 8,
            marginTop: 40,
            marginBottom: 20,
            x: { type: 'linear', domain: [0, 9.2], axis: null },
            y: { type: 'utc', domain: [timelineStart, timelineEnd], reverse: true, ticks: yearStarts, tickFormat: '%Y', label: null, grid: true },
            marks: [
              Plot.text([{ x: 0.7, text: 'Directa' }, { x: 2.7, text: 'Convenios' }], { x: 'x', text: 'text', frameAnchor: 'top', dy: -22, fontWeight: 700, fontSize: 12 }),
              Plot.rect(directRestrictions, { x1: 0.3, x2: 1.1, y1: 'start', y2: 'end', ...restrictionStyle.direct }),
              Plot.rect(interadministrativeRestrictions, { x1: 2.3, x2: 3.1, y1: 'start', y2: 'end', ...restrictionStyle.interadministrative }),
              Plot.text(stackedLabels, { x: 3.5, y: 'at', text: 'label', textAnchor: 'start', fontSize: 13, ...halo }),
              ...(cutoffDate
                ? [
                    Plot.ruleY([cutoffDate], { x1: 0, x2: 3.4, stroke: 'var(--ink)', strokeWidth: 2, strokeDasharray: '6 4' }),
                    Plot.text([cutoffDate], { x: 3.4, y: (d: Date) => d, text: () => 'Fecha de corte', textAnchor: 'end', lineAnchor: 'bottom', dy: -4, fontWeight: 700 }),
                  ]
                : []),
            ],
          },
  },
];

export const getFigure = (id: string): FigureSpec => {
  const figure = FIGURES.find((candidate) => candidate.id === id);
  if (!figure) throw new Error(`Figura desconocida: ${id}`);
  return figure;
};
