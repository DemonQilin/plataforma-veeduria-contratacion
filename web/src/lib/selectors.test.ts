// S6: los selectores solo eligen celdas; no calculan (regla 2 de CLAUDE.md). Indicador I2.
import { describe, expect, it } from 'vitest';
import type {
  ElectoralRestriction,
  IndicatorCell,
  MonthlySeriesRow,
  ReconciliationMonth,
} from '../types/contract';
import {
  comparisonRoles,
  comparisonWindows,
  directAwardJanuary,
  directAwardMonthly,
  explorerCells,
  i2ByYear,
  i2Extremes,
  reconciliationMonths,
  restrictions,
} from './selectors';

const cell = (over: Partial<IndicatorCell>): IndicatorCell => ({
  denominator: 100,
  department: null,
  indicator: 'I2',
  is_suppressed: false,
  level: 'district',
  measure: 'count',
  numerator: 50,
  period: '2022',
  ratio: 0.5,
  sample_size: 100,
  variant: null,
  ...over,
});

const windows = [
  { year: 2022, role: 'treatment' },
  { year: 2023, role: 'control' },
] as const;

describe('i2ByYear', () => {
  const cells = [
    cell({ period: '2023', ratio: 0.25 }),
    cell({ period: '2022', ratio: 0.58 }),
    cell({ period: '2022', measure: 'value', ratio: 0.3 }),
    cell({ period: '2022', variant: 'service_contract', ratio: 0.9 }),
    cell({ period: '2022', indicator: 'I1', ratio: 0.1 }),
    cell({ period: '2022', level: 'department', department: 'x', ratio: 0.7 }),
  ];

  it('elige solo I2 del Distrito con esa variante y medida, por año, con su papel', () => {
    const result = i2ByYear({ variant: null, measure: 'count' }, cells, windows);
    expect(result.map((r) => [r.year, r.role, r.cell.ratio])).toEqual([
      [2022, 'treatment', 0.58],
      [2023, 'control', 0.25],
    ]);
  });

  it('con variante no mezcla otras variantes ni la base', () => {
    const result = i2ByYear({ variant: 'service_contract', measure: 'count' }, cells, windows);
    expect(result.map((r) => r.cell.ratio)).toEqual([0.9]);
  });

  it('devuelve la celda tal cual, suprimida incluida', () => {
    const suppressed = cell({ is_suppressed: true, ratio: null, sample_size: 3 });
    const [row] = i2ByYear({ variant: null, measure: 'count' }, [suppressed], windows);
    expect(row?.cell).toBe(suppressed);
  });
});

describe('restrictions', () => {
  const list = [
    { cycle: 'b', scope: 'interadministrative', start: '2023-06-29' },
    { cycle: 'a', scope: 'direct_award', start: '2022-01-29' },
    { cycle: 'c', scope: 'direct_award', start: '2026-01-31' },
  ] as unknown as ElectoralRestriction[];

  it('ordena por inicio', () => {
    expect(restrictions(undefined, list).map((r) => r.cycle)).toEqual(['a', 'b', 'c']);
  });

  it('filtra por alcance', () => {
    expect(restrictions('direct_award', list).map((r) => r.cycle)).toEqual(['a', 'c']);
  });
});

describe('directAwardMonthly', () => {
  const row = (over: Partial<MonthlySeriesRow>): MonthlySeriesRow => ({
    contract_count: 1,
    contract_type: null,
    is_suppressed: false,
    period: '2022-01',
    procurement_method: 'direct_award',
    value: 1,
    value_sample_size: 1,
    ...over,
  });

  it('solo contratación directa sin tipo de contrato', () => {
    const rows = [
      row({}),
      row({ contract_type: 'service_contract' }),
      row({ procurement_method: 'public_tender' }),
    ];
    expect(directAwardMonthly(rows)).toEqual([rows[0]]);
  });
});

describe('directAwardJanuary', () => {
  const row = (period: string): MonthlySeriesRow => ({
    contract_count: 1,
    contract_type: null,
    is_suppressed: false,
    period,
    procurement_method: 'direct_award',
    value: 1,
    value_sample_size: 1,
  });

  it('elige solo los meses de enero, en orden', () => {
    const rows = [row('2023-01'), row('2022-02'), row('2022-01')];
    expect(directAwardJanuary(rows).map((r) => r.period)).toEqual(['2022-01', '2023-01']);
  });
});

describe('i2Extremes', () => {
  const years = i2ByYear(
    { variant: null, measure: 'count' },
    [
      cell({ period: '2022', ratio: 0.58 }),
      cell({ period: '2023', ratio: 0.25 }),
      cell({ period: '2024', ratio: 0.18 }),
    ],
    [
      { year: 2022, role: 'treatment' },
      { year: 2023, role: 'control' },
      { year: 2024, role: 'control' },
    ],
  );

  it('devuelve las celdas menor y mayor de un papel, sin recalcular', () => {
    const { min, max } = i2Extremes(years, 'control');
    expect([min?.cell.ratio, max?.cell.ratio]).toEqual([0.18, 0.25]);
    expect(max?.cell).toBe(years[1]?.cell);
  });

  it('sin filas devuelve undefined', () => {
    expect(i2Extremes([], 'control')).toEqual({ min: undefined, max: undefined });
  });
});

describe('con las salidas reales', () => {
  it('I2 base por número cubre 2022 a 2026 y marca 2022 y 2026 como tratamiento', () => {
    const result = i2ByYear({ variant: null, measure: 'count' });
    expect(result.map((r) => [r.year, r.role])).toEqual([
      [2022, 'treatment'],
      [2023, 'control'],
      [2024, 'control'],
      [2025, 'control'],
      [2026, 'treatment'],
    ]);
  });
});

describe('comparisonRoles', () => {
  it('une el papel de cada año con su año, sin calcular', () => {
    const roles = comparisonRoles([
      { year: 2022, role: 'treatment' },
      { year: 2023, role: 'control' },
    ]);
    expect(roles.get(2022)).toBe('treatment');
    expect(roles.get(2023)).toBe('control');
    expect(roles.get(2024)).toBeUndefined();
  });
});

describe('comparisonWindows', () => {
  it('ordena por año y devuelve las ventanas tal cual', () => {
    const windows = comparisonWindows([
      { year: 2024, role: 'control', window_start: '2024-01-01', window_end: '2024-01-29', denominator_end: '2024-10-30', reference_restriction_end: '2024-06-20' },
      { year: 2022, role: 'treatment', window_start: '2022-01-01', window_end: '2022-01-28', denominator_end: '2022-10-30', reference_restriction_end: '2022-06-19' },
    ]);
    expect(windows.map((window) => window.year)).toEqual([2022, 2024]);
    expect(windows[0]?.window_end).toBe('2022-01-28');
  });
});

// R15: la conciliación SECOP–MEData llega calculada; el selector solo ordena.
describe('reconciliationMonths', () => {
  const month = (over: Partial<ReconciliationMonth>): ReconciliationMonth => ({
    below_threshold: false,
    medata_count: 10,
    medata_coverage: 1,
    period: '2022-01',
    secop_count: 10,
    secop_coverage: 1,
    shared_count: 10,
    shared_share: 1,
    union_count: 10,
    ...over,
  });

  it('ordena por periodo y devuelve cada mes tal cual, con su marca de umbral', () => {
    const result = reconciliationMonths([
      month({ period: '2022-03', below_threshold: true, shared_share: 0.67 }),
      month({ period: '2022-01' }),
    ]);
    expect(result.map((m) => m.period)).toEqual(['2022-01', '2022-03']);
    expect(result[1]).toMatchObject({ below_threshold: true, shared_share: 0.67 });
  });
});

describe('explorerCells', () => {
  const cells = [
    cell({ indicator: 'I1', period: '2023' }),
    cell({ indicator: 'I1', period: '2022' }),
    cell({ indicator: 'I1', period: '2022', variant: 'non_competitive' as never }),
    cell({ indicator: 'I1', period: '2022', measure: 'value' }),
    cell({ indicator: 'I4', period: '2022', measure: 'value' }),
    cell({ indicator: 'I4', period: '2022', measure: 'count' }),
    cell({ indicator: 'I2', period: '2022' }),
  ];

  it('elige la variante base y la medida de cada indicador, por año', () => {
    expect(explorerCells('I1', cells).map((c) => [c.indicator, c.period, c.measure])).toEqual([
      ['I1', '2022', 'count'],
      ['I1', '2023', 'count'],
    ]);
    expect(explorerCells('I4', cells).map((c) => c.measure)).toEqual(['value']);
  });
});
