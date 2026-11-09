// Fuente única de cada figura: el componente (SVG y tabla) y el CSV la leen,
// así que tabla y CSV no pueden diferir (docs/adr/0048).
import type { PlotOptions } from '@observablehq/plot';
import * as Plot from '@observablehq/plot';
import { getMetadata } from './data';
import { formatDate, formatMonth, formatNumber, formatPercent } from './format';
import type { I2Selection } from './selectors';
import { comparisonRoles, directAwardJanuary, directAwardMonthly, i2ByYear, restrictions } from './selectors';

export type Cell = string | number | null;

export interface FigureColumn {
  key: string;
  label: string;
  kind: 'text' | 'number' | 'percent';
  /** El valor sale vacío y se escribe «datos insuficientes» cuando la fila está suprimida. */
  suppressible?: boolean;
}

export interface FigureRow {
  values: Record<string, Cell>;
  is_suppressed: boolean;
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

// Pantalla 3: serie mensual de contratación directa con las restricciones detrás de las barras.
// El papel del año viene de comparison_windows; no se calcula (S6).
const roles = comparisonRoles();
const monthlyWithDate = directMonthlyRows.map((row) => ({
  ...row,
  date: new Date(`${row.period}-01T00:00:00Z`),
  role: roles.get(Number(row.period.slice(0, 4))),
}));
const monthlyTreatment = monthlyWithDate.filter((row) => row.role === 'treatment');
const monthlyControl = monthlyWithDate.filter((row) => row.role === 'control');
const lastMonth = monthlyWithDate.at(-1)?.date ?? new Date(Date.UTC(2026, 9, 1));
const monthlyStart = new Date(Date.UTC(monthlyWithDate[0]?.date.getUTCFullYear() ?? 2022, 0, 1));
const monthlyEnd = new Date(Date.UTC(lastMonth.getUTCFullYear(), lastMonth.getUTCMonth() + 1, 1));
const monthlyYearStarts = Array.from(
  { length: monthlyEnd.getUTCFullYear() - monthlyStart.getUTCFullYear() + 1 },
  (_, index) => new Date(Date.UTC(monthlyStart.getUTCFullYear() + index, 0, 1)),
).filter((date) => date < monthlyEnd);
const monthlyYMax = Math.max(...directMonthlyRows.map((row) => row.contract_count)) * 1.1;
const januaryPeaks = directAwardJanuary(directMonthlyRows).map((row) => ({
  ...row,
  date: new Date(`${row.period}-01T00:00:00Z`),
}));
const directMonthlyRestrictions = directRestrictions;
const interadministrativeMonthly = interadministrativeRestrictions;
const firstPeriod = directMonthlyRows[0]?.period ?? '';
const lastPeriod = directMonthlyRows.at(-1)?.period ?? '';
const monthlyTitle = `Contratos directos firmados por mes, de ${formatMonth(firstPeriod)} a ${formatMonth(lastPeriod)}`;
const monthlyDescription =
  `Gráfico de barras: contratos de contratación directa firmados por mes, de ${formatMonth(firstPeriod)} a ${formatMonth(lastPeriod)}. ` +
  `Cada barra es un mes; las naranjas son años con elecciones y las grises, años de comparación. ` +
  `Enero: ${januaryPeaks.map((row) => `${formatNumber(row.contract_count)} en ${row.period.slice(0, 4)}`).join(', ')}. ` +
  `La restricción de contratación directa va sombreada: ${rangesOf(true)}.`;

// Pantalla 4: I2 del Distrito por año, elecciones frente a comparación. Elige las celdas de
// indicators.json (S6); el eje de 0 a 100 % es escala visual y no cambia entre medidas.
const roleName = (role: string | undefined) =>
  role === 'treatment' ? 'Elecciones' : role === 'control' ? 'Comparación' : '';
const i2Figure = (
  id: string,
  selection: I2Selection,
  title: string,
  intro: string,
  withValueSample = false,
  labels: { numerator?: string; denominator?: string; axis?: string } = {},
): FigureSpec => {
  const years = i2ByYear(selection).map((year) => ({
    ...year,
    name: String(year.year),
    ratio: year.cell.ratio,
    shown: year.cell.ratio === null ? 0 : year.cell.ratio,
    label: year.cell.ratio === null ? '' : formatPercent(year.cell.ratio),
  }));
  const domain = years.map((year) => year.name);
  const treatment = years.filter((year) => year.role === 'treatment');
  const control = years.filter((year) => year.role === 'control');
  const unit = selection.measure === 'value' ? 'pesos' : 'contratos';
  const parts = years.map(
    (year) =>
      `${year.name}, ${year.ratio === null ? 'datos insuficientes' : formatPercent(year.ratio)} (${formatNumber(year.cell.numerator ?? 0)} de ${formatNumber(year.cell.denominator ?? 0)} ${unit}; ${roleName(year.role).toLowerCase()})`,
  );
  return {
    id,
    title,
    description: `${intro} ${parts.join('; ')}. Las barras naranjas son años con elecciones; las grises, años de comparación.`,
    columns: [
      { key: 'year', label: 'Año', kind: 'text' },
      { key: 'role', label: 'Papel', kind: 'text' },
      { key: 'ratio', label: 'Proporción', kind: 'percent', suppressible: true },
      { key: 'numerator', label: labels.numerator ?? (selection.measure === 'value' ? 'Valor en la ventana (COP)' : 'Contratos en la ventana'), kind: 'number', suppressible: true },
      { key: 'denominator', label: labels.denominator ?? (selection.measure === 'value' ? 'Valor total (COP)' : 'Contratos en total'), kind: 'number', suppressible: true },
      ...(withValueSample ? ([{ key: 'sample_size', label: 'Contratos con valor', kind: 'number' }] as const) : []),
    ],
    sampleKey: 'sample_size',
    responsive: true,
    rows: years.map((year) => ({
      is_suppressed: year.cell.is_suppressed,
      values: {
        year: year.name,
        role: roleName(year.role),
        ratio: year.ratio,
        numerator: year.cell.numerator,
        denominator: year.cell.denominator,
        sample_size: year.cell.sample_size,
      },
    })),
    plot: (size) => {
      const small = size === 'small';
      const base = {
        width: small ? 360 : 640,
        height: small ? 320 : 380,
        marginTop: labels.axis && !small ? 44 : 28,
        marginLeft: small ? 44 : 56,
        marginRight: small ? 56 : 16,
      };
      const text = { text: 'label', fontWeight: 700, fontSize: small ? 12 : 13, ...halo } as const;
      return small
        ? {
            ...base,
            x: { domain: [0, 1], label: null, grid: true, tickFormat: '.0%' },
            y: { domain, label: null },
            marks: [
              Plot.barX(treatment, { y: 'name', x: 'shown', fill: 'var(--chart-treatment)' }),
              Plot.barX(control, { y: 'name', x: 'shown', fill: 'var(--chart-control)' }),
              Plot.ruleX([0]),
              Plot.text(years, { y: 'name', x: 'shown', textAnchor: 'start', dx: 6, ...text }),
            ],
          }
        : {
            ...base,
            x: { domain, label: null },
            y: { domain: [0, 1], label: labels.axis ?? 'Proporción en la ventana de enero', grid: true, tickFormat: '.0%' },
            marks: [
              Plot.barY(treatment, { x: 'name', y: 'shown', fill: 'var(--chart-treatment)' }),
              Plot.barY(control, { x: 'name', y: 'shown', fill: 'var(--chart-control)' }),
              Plot.ruleY([0]),
              Plot.text(years, { x: 'name', y: 'shown', dy: -10, ...text }),
            ],
          };
    },
  };
};
// Pantalla 5.1: I2 por tipo de contrato. Una fila por año y tipo, cada una con su celda (y su
// supresión). Prestación de servicios va con barra llena y el resto con borde (S6: solo elige).
const typeNames = { service_contract: 'Prestación de servicios', non_service_contract: 'Resto de tipos' } as const;
const byTypeFigure = (): FigureSpec => {
  const series = (['service_contract', 'non_service_contract'] as const).flatMap((variant) =>
    i2ByYear({ variant, measure: 'count' }).map((year) => ({
      ...year,
      variant,
      type: typeNames[variant],
      name: String(year.year),
      ratio: year.cell.ratio,
      shown: year.cell.ratio === null ? 0 : year.cell.ratio,
      label: year.cell.ratio === null ? '' : formatPercent(year.cell.ratio),
      color: year.role === 'treatment' ? 'var(--chart-treatment)' : 'var(--chart-control)',
    })),
  );
  const domain = [...new Set(series.map((item) => item.name))];
  const filled = series.filter((item) => item.variant === 'service_contract');
  const outlined = series.filter((item) => item.variant === 'non_service_contract');
  const yearsOf = (variant: keyof typeof typeNames) =>
    series
      .filter((item) => item.variant === variant)
      .map((item) => `${item.ratio === null ? 'datos insuficientes' : formatPercent(item.ratio)} en ${item.name}`)
      .join(', ');
  return {
    id: 'concentracion-enero-por-tipo',
    title: 'Contratación directa firmada en la ventana de enero, por tipo de contrato',
    description:
      `Gráfico de barras: parte de la contratación directa firmada en la ventana de enero, por número de contratos y según el tipo de contrato. ` +
      `Prestación de servicios: ${yearsOf('service_contract')}. Resto de tipos de contrato: ${yearsOf('non_service_contract')}. ` +
      `La barra llena es la prestación de servicios y la barra con borde, el resto de tipos; las naranjas son años con elecciones y las grises, años de comparación.`,
    columns: [
      { key: 'year', label: 'Año', kind: 'text' },
      { key: 'role', label: 'Papel', kind: 'text' },
      { key: 'type', label: 'Tipo de contrato', kind: 'text' },
      { key: 'ratio', label: 'Proporción', kind: 'percent', suppressible: true },
      { key: 'numerator', label: 'Contratos en la ventana', kind: 'number', suppressible: true },
      { key: 'denominator', label: 'Contratos en total', kind: 'number', suppressible: true },
    ],
    responsive: true,
    rows: domain.flatMap((name) =>
      series
        .filter((item) => item.name === name)
        .map((item) => ({
          is_suppressed: item.cell.is_suppressed,
          values: {
            year: item.name,
            role: roleName(item.role),
            type: item.type,
            ratio: item.ratio,
            numerator: item.cell.numerator,
            denominator: item.cell.denominator,
          },
        })),
    ),
    plot: (size) => {
      const small = size === 'small';
      const text = { text: 'label', fontWeight: 700, fontSize: small ? 11 : 12, ...halo } as const;
      const fillOf = { fill: 'color' } as const;
      const outlineOf = { fill: 'var(--surface-raised)', stroke: 'color', strokeWidth: 2 } as const;
      return small
        ? {
            width: 360,
            height: 440,
            marginTop: 28,
            marginLeft: 44,
            marginRight: 56,
            x: { domain: [0, 1], label: null, grid: true, tickFormat: '.0%' },
            y: { axis: null, domain: ['service_contract', 'non_service_contract'] },
            fy: { domain, label: null },
            marks: [
              Plot.barX(filled, { fy: 'name', y: 'variant', x: 'shown', ...fillOf }),
              Plot.barX(outlined, { fy: 'name', y: 'variant', x: 'shown', ...outlineOf }),
              Plot.ruleX([0]),
              Plot.text(series, { fy: 'name', y: 'variant', x: 'shown', textAnchor: 'start', dx: 6, ...text }),
            ],
          }
        : {
            width: 640,
            height: 380,
            marginTop: 28,
            marginLeft: 56,
            marginRight: 16,
            x: { axis: null, domain: ['service_contract', 'non_service_contract'] },
            fx: { domain, label: null },
            y: { domain: [0, 1], label: 'Proporción en la ventana de enero', grid: true, tickFormat: '.0%' },
            marks: [
              Plot.barY(filled, { fx: 'name', x: 'variant', y: 'shown', ...fillOf }),
              Plot.barY(outlined, { fx: 'name', x: 'variant', y: 'shown', ...outlineOf }),
              Plot.ruleY([0]),
              Plot.text(series, { fx: 'name', x: 'variant', y: 'shown', dy: -10, ...text }),
            ],
          };
    },
  };
};
const i2Titles = {
  count: 'Contratación directa firmada en la ventana de enero, por número de contratos',
  value: 'Contratación directa firmada en la ventana de enero, por valor',
  excluding: 'Contratación directa firmada en la ventana de enero, sin convenios interadministrativos',
} as const;

export const FIGURES: readonly FigureSpec[] = [
  i2Figure('concentracion-enero-por-numero', { variant: null, measure: 'count' }, i2Titles.count, 'Gráfico de barras: parte de la contratación directa firmada en la ventana de enero, por número de contratos.'),
  i2Figure('concentracion-enero-por-valor', { variant: null, measure: 'value' }, i2Titles.value, 'Gráfico de barras: parte del valor de la contratación directa firmada en la ventana de enero, sin operaciones de crédito público.', true),
  i2Figure('concentracion-enero-sin-interadministrativos', { variant: 'excluding_interadministrative', measure: 'count' }, i2Titles.excluding, 'Gráfico de barras: parte de la contratación directa firmada en la ventana de enero, por número de contratos y sin convenios interadministrativos.'),
  byTypeFigure(),
  i2Figure(
    'contratos-enero-despues-de-la-restriccion',
    { variant: 'spans_restriction', measure: 'count' },
    'Contratos de enero que terminan después de la restricción de referencia',
    'Gráfico de barras: parte de los contratos directos firmados en la ventana de enero cuyo plazo termina después del fin de la restricción de referencia, por número de contratos. Resultado no concluyente.',
    false,
    { numerator: 'Terminan después de la restricción', denominator: 'Contratos firmados en la ventana', axis: 'Terminan después de la restricción' },
  ),
  {
    id: 'contratacion-directa-por-mes',
    title: monthlyTitle,
    description: monthlyDescription,
    columns: [
      { key: 'period', label: 'Mes', kind: 'text' },
      { key: 'contract_count', label: 'Contratos', kind: 'number' },
      { key: 'value', label: 'Valor (COP)', kind: 'number', suppressible: true },
    ],
    sampleKey: 'value_sample_size',
    responsive: true,
    rows: directMonthlyRows.map((row) => ({
      is_suppressed: row.is_suppressed,
      values: {
        period: formatMonth(row.period),
        contract_count: row.contract_count,
        value: row.value,
        value_sample_size: row.value_sample_size,
      },
    })),
    plot: (size) => {
      const small = size === 'small';
      return {
        width: small ? 360 : 960,
        height: small ? 300 : 380,
        marginLeft: small ? 40 : 56,
        marginRight: small ? 8 : 16,
        marginTop: 24,
        x: { type: 'utc', domain: [monthlyStart, monthlyEnd], ticks: monthlyYearStarts, tickFormat: '%Y', label: null },
        y: { label: small ? null : 'Contratos por mes', grid: true },
        marks: [
          Plot.rect(directMonthlyRestrictions, { x1: 'start', x2: 'end', y1: 0, y2: monthlyYMax, fill: 'var(--chart-restriction)', clip: true }),
          Plot.rect(interadministrativeMonthly, { x1: 'start', x2: 'end', y1: 0, y2: monthlyYMax, ...restrictionStyle.interadministrative, clip: true }),
          Plot.rectY(monthlyTreatment, { x: 'date', interval: 'month', y: 'contract_count', fill: 'var(--chart-treatment)' }),
          Plot.rectY(monthlyControl, { x: 'date', interval: 'month', y: 'contract_count', fill: 'var(--chart-control)' }),
          Plot.ruleY([0]),
          Plot.text(januaryPeaks, { x: 'date', y: 'contract_count', text: (d) => formatNumber(d.contract_count), dy: -8, fontWeight: 700, fontSize: small ? 11 : 13, ...halo }),
        ],
      };
    },
  },
  {
    id: 'periodos-de-restriccion',
    title: `Periodos de restricción de la Ley de Garantías, de ${timelineStart.getUTCFullYear()} a ${timelineEnd.getUTCFullYear() - 1}`,
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
      is_suppressed: false,
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
