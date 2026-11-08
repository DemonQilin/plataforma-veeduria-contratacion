// S6: los selectores solo eligen celdas; no calculan (regla 2 de CLAUDE.md). Indicador I2.
import { describe, expect, it } from 'vitest';
import type { ElectoralRestriction, IndicatorCell, MonthlySeriesRow } from '../types/contract';
import { directAwardMonthly, i2ByYear, restrictions } from './selectors';

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
