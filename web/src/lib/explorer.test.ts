// S6: el explorador solo elige, ordena y da formato; no calcula. Indicadores I1, I3, I4 e I5.
import { describe, expect, it } from 'vitest';
import type { IndicatorCell } from '../types/contract';
import { buildExplorer } from './explorer';

const cell = (over: Partial<IndicatorCell>): IndicatorCell => ({
  denominator: 100,
  department: null,
  indicator: 'I1',
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
const dep = (department: string, over: Partial<IndicatorCell>) =>
  cell({ level: 'department', department, ...over });

describe('buildExplorer', () => {
  const cells = [
    cell({ period: '2022', ratio: 0.8, numerator: 80 }),
    dep('health', { ratio: 0.2, numerator: 20 }),
    dep('education', { ratio: 0.9, numerator: 90 }),
    dep('tourism', { is_suppressed: true, ratio: null, numerator: null, denominator: null, sample_size: 3 }),
    dep('mobility', { ratio: 0.5, numerator: 50, variant: 'non_competitive' }),
    dep('mobility', { ratio: 0.5, numerator: 50, measure: 'value' }),
    cell({ indicator: 'I5', period: '2023', ratio: 0.1, numerator: 10 }),
    cell({ indicator: 'I4', measure: 'value', period: '2022', ratio: 0.4, numerator: 4e9, denominator: 1e10, sample_size: 914 }),
    dep('health', { indicator: 'I3', period: '2022', ratio: 0.3, numerator: 3, denominator: 10, sample_size: 10 }),
  ];
  const data = buildExplorer(cells, '2026-10-30');
  const i1 = data.indicators.find((i) => i.id === 'I1')!;
  const year = i1.periods[0]!;

  it('ofrece I1, I3, I4 e I5 y no otros indicadores', () => {
    expect(data.indicators.map((i) => i.id)).toEqual(['I1', 'I3', 'I4', 'I5']);
  });

  it('separa el Distrito de las secretarías y descarta variantes y otras medidas', () => {
    expect(year.district?.display).toBe('80%');
    expect(year.departments.map((row) => row.code)).toEqual(['education', 'health', 'tourism']);
  });

  it('ordena de mayor a menor y deja las suprimidas al final', () => {
    expect(year.departments.map((row) => row.display)).toEqual(['90%', '20%', 'datos insuficientes']);
  });

  it('muestra la base de cada cifra y el n de la suprimida', () => {
    expect(year.district?.note).toBe('80 de 100 contratos');
    const suppressed = year.departments.at(-1)!;
    expect(suppressed).toMatchObject({ isSuppressed: true, label: 'Turismo y Entretenimiento', note: '3 contratos', width: 0 });
  });

  it('I3 cuenta procesos e I4 muestra los contratos en que se basa', () => {
    const i3 = data.indicators.find((i) => i.id === 'I3')!;
    expect(i3.periods[0]!.departments[0]!.note).toBe('3 de 10 procesos');
    const i4 = data.indicators.find((i) => i.id === 'I4')!;
    expect(i4.periods[0]!.district?.note).toBe('914 contratos');
  });

  it('cada indicador trae solo los años que tiene (I5: 2023)', () => {
    const i5 = data.indicators.find((i) => i.id === 'I5')!;
    expect(i5.periods.map((y) => y.period)).toEqual(['2023']);
  });

  it('lleva la fecha de corte', () => {
    expect(data.cutoffDate).toBe('2026-10-30');
  });
});
