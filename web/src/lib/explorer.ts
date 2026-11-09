// Pantalla 6: arma en el build lo que necesita la isla del explorador. Solo elige, ordena y
// da formato (S6, regla 2 de CLAUDE.md); la isla no calcula ni formatea.
import type { IndicatorCell } from '../types/contract';
import { getIndicators, getMetadata } from './data';
import { departmentLabel } from './departments';
import { formatNumber, formatPercent } from './format';
import type { ExplorerIndicator } from './selectors';
import { explorerCells } from './selectors';

export interface ExplorerRow {
  code: string | null;
  label: string;
  /** Cifra ya formateada, o «datos insuficientes» (R13). */
  display: string;
  /** La base de la cifra: «387 de 1.632 contratos». */
  note: string;
  /** Ancho de la barra, 0 a 72 (escala visual, no una cifra publicada). */
  width: number;
  isSuppressed: boolean;
}

export interface ExplorerPeriod {
  period: string;
  district: ExplorerRow | null;
  departments: ExplorerRow[];
}

export interface ExplorerIndicatorData {
  id: ExplorerIndicator;
  title: string;
  question: string;
  periods: ExplorerPeriod[];
}

export interface ExplorerData {
  /** Fecha de corte en ISO. */
  cutoffDate: string;
  indicators: ExplorerIndicatorData[];
}

// Preguntas de docs/indicadores.md §1; `unit` es lo que cuenta el n de cada indicador.
const INDICATORS: readonly { id: ExplorerIndicator; title: string; question: string; unit: string }[] = [
  { id: 'I1', title: 'Contratación directa', question: '¿Cuánto se contrata sin competencia?', unit: 'contratos' },
  { id: 'I3', title: 'Un solo oferente', question: 'En los procesos con competencia, ¿cuántas veces se presentó una sola empresa?', unit: 'procesos' },
  { id: 'I4', title: 'Concentración de proveedores', question: '¿Unas pocas empresas reciben buena parte del dinero?', unit: 'contratos' },
  { id: 'I5', title: 'Adiciones', question: '¿Cuánto crecen los contratos después de firmados?', unit: 'contratos' },
];

const SUPPRESSED = 'datos insuficientes';
const SCALE = 72;

function toRow(cell: IndicatorCell, unit: string, indicator: ExplorerIndicator): ExplorerRow {
  const code = cell.department;
  const label = code === null ? 'Distrito' : departmentLabel(code);
  if (cell.is_suppressed || cell.ratio === null) {
    return { code, label, display: SUPPRESSED, note: `${formatNumber(cell.sample_size)} ${unit}`, width: 0, isSuppressed: true };
  }
  // En I4 numerador y denominador son pesos: la base que se muestra es el número de contratos.
  const note =
    indicator === 'I4'
      ? `${formatNumber(cell.sample_size)} ${unit}`
      : `${formatNumber(cell.numerator ?? 0)} de ${formatNumber(cell.denominator ?? 0)} ${unit}`;
  return { code, label, display: formatPercent(cell.ratio), note, width: cell.ratio * SCALE, isSuppressed: false };
}

// De mayor a menor; las suprimidas al final; empate por nombre.
const byRatioDesc = (cells: Map<string, number>) => (a: ExplorerRow, b: ExplorerRow) =>
  a.isSuppressed !== b.isSuppressed
    ? a.isSuppressed ? 1 : -1
    : (cells.get(b.label) ?? 0) - (cells.get(a.label) ?? 0) || a.label.localeCompare(b.label, 'es-CO');

export function buildExplorer(
  cells: readonly IndicatorCell[] = getIndicators()?.cells ?? [],
  cutoffDate: string = getMetadata()?.cutoff_date ?? '',
): ExplorerData {
  const indicators = INDICATORS.map(({ id, title, question, unit }) => {
    const selected = explorerCells(id, cells);
    const periodIds = [...new Set(selected.map((cell) => cell.period))];
    const periods = periodIds.map((period) => {
      const ofPeriod = selected.filter((cell) => cell.period === period);
      const ratios = new Map(
        ofPeriod.flatMap((cell) =>
          cell.ratio === null ? [] : [[cell.department === null ? 'Distrito' : departmentLabel(cell.department), cell.ratio] as const],
        ),
      );
      const district = ofPeriod.find((cell) => cell.level === 'district');
      return {
        period,
        district: district ? toRow(district, unit, id) : null,
        departments: ofPeriod
          .filter((cell) => cell.level === 'department')
          .map((cell) => toRow(cell, unit, id))
          .toSorted(byRatioDesc(ratios)),
      };
    });
    return { id, title, question, periods };
  });
  return { cutoffDate, indicators };
}
