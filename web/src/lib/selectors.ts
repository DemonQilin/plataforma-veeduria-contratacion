// Elige celdas de data/outputs/. No calcula ni filtra por reglas de negocio
// (regla 2 de CLAUDE.md, S6): solo selecciona por llave y ordena para mostrar.
// Cada selector recibe los datos por parámetro (por defecto, las salidas reales).
import type {
  ComparisonYear,
  ElectoralRestriction,
  IndicatorCell,
  MonthlySeriesRow,
} from '../types/contract';
import { getElectoralCalendar, getIndicators, getMonthlySeries } from './data';

/** Variantes de I2 que usan las pantallas 4 y 5 (`null` es la base). */
export type I2Variant =
  | 'service_contract'
  | 'non_service_contract'
  | 'spans_restriction'
  | 'excluding_interadministrative';

export interface I2Selection {
  variant: I2Variant | null;
  measure: 'count' | 'value';
}

export interface I2YearCell {
  year: number;
  /** Papel del año en la comparación (`electoral_calendar.json`). */
  role: ComparisonYear['role'] | undefined;
  cell: IndicatorCell;
}

/** I2 del Distrito por año, con la celda tal cual (suprimida incluida). */
export function i2ByYear(
  { variant, measure }: I2Selection,
  cells: readonly IndicatorCell[] = getIndicators()?.cells ?? [],
  windows: readonly Pick<ComparisonYear, 'year' | 'role'>[] = getElectoralCalendar()
    ?.comparison_windows ?? [],
): I2YearCell[] {
  return cells
    .filter(
      (cell) =>
        cell.indicator === 'I2' &&
        cell.level === 'district' &&
        cell.variant === variant &&
        cell.measure === measure,
    )
    .map((cell) => ({
      year: Number(cell.period),
      role: windows.find((window) => window.year === Number(cell.period))?.role,
      cell,
    }))
    .sort((a, b) => a.year - b.year);
}

/** Periodos de la Ley de Garantías por inicio, de un alcance o de todos. */
export function restrictions(
  scope?: ElectoralRestriction['scope'],
  list: readonly ElectoralRestriction[] = getElectoralCalendar()?.restrictions ?? [],
): ElectoralRestriction[] {
  return list
    .filter((restriction) => scope === undefined || restriction.scope === scope)
    .toSorted((a, b) => a.start.localeCompare(b.start));
}

/** Contratación directa por mes, todos los tipos de contrato (celdas sin `contract_type`). */
export function directAwardMonthly(
  rows: readonly MonthlySeriesRow[] = getMonthlySeries()?.rows ?? [],
): MonthlySeriesRow[] {
  return rows.filter((row) => row.procurement_method === 'direct_award' && row.contract_type === null);
}

/** Contratación directa de enero de cada año (periodos `AAAA-01`), en orden. */
export function directAwardJanuary(
  rows: readonly MonthlySeriesRow[] = directAwardMonthly(),
): MonthlySeriesRow[] {
  return rows.filter((row) => row.period.endsWith('-01')).toSorted((a, b) => a.period.localeCompare(b.period));
}

/** Celdas con la razón menor y mayor entre los años de un papel (no calcula: elige). */
export function i2Extremes(
  years: readonly I2YearCell[],
  role: ComparisonYear['role'],
): { min: I2YearCell | undefined; max: I2YearCell | undefined } {
  const sorted = years
    .filter((year) => year.role === role && year.cell.ratio !== null)
    .toSorted((a, b) => (a.cell.ratio ?? 0) - (b.cell.ratio ?? 0));
  return { min: sorted[0], max: sorted.at(-1) };
}
