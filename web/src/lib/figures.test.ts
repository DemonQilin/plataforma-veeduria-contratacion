// T5 (S7, pantalla 2): la figura de periodos de restricción solo presenta celdas de
// electoral_calendar.json; la de T2 sigue igual (S6).
import { describe, expect, it } from 'vitest';
import { toCsv } from './csv';
import { getFigure } from './figures';
import { getIndicators } from './data';

describe('periodos-de-restriccion', () => {
  const figure = getFigure('periodos-de-restriccion');

  it('es responsiva: un SVG para celular y otro para escritorio', () => {
    expect(figure.responsive).toBe(true);
  });

  it('tiene una fila por restricción, en orden de inicio, con textos en español', () => {
    expect(figure.rows.map((row) => row.values)).toEqual([
      { scope: 'Contratación directa', start: '29 de enero de 2022', end: '19 de junio de 2022', status: 'Terminada' },
      { scope: 'Convenios interadministrativos', start: '29 de junio de 2023', end: '29 de octubre de 2023', status: 'Terminada' },
      { scope: 'Convenios interadministrativos', start: '8 de noviembre de 2025', end: '8 de marzo de 2026', status: 'Terminada' },
      { scope: 'Contratación directa', start: '31 de enero de 2026', end: '21 de junio de 2026', status: 'Terminada' },
      { scope: 'Convenios interadministrativos', start: '30 de junio de 2027', end: '31 de octubre de 2027', status: 'Próxima' },
    ]);
  });

  it('ninguna fila está suprimida', () => {
    expect(figure.rows.every((row) => !row.is_suppressed)).toBe(true);
  });

  it('la descripción en texto menciona la fecha de corte y no es un marcador', () => {
    expect(figure.description).toContain('30 de octubre de 2026');
    expect(figure.description).not.toContain('[Texto pendiente');
  });
});

describe('contratacion-directa-por-mes (T6, pantalla 3)', () => {
  const figure = getFigure('contratacion-directa-por-mes');

  it('es responsiva: un SVG para celular y otro para escritorio', () => {
    expect(figure.responsive).toBe(true);
  });

  it('el título nombra el primer y el último mes', () => {
    expect(figure.title).toContain('enero de 2022');
    expect(figure.title).toContain('octubre de 2026');
  });

  it('la columna Mes va en español', () => {
    expect(figure.rows[0]?.values.period).toBe('enero de 2022');
  });

  it('la descripción no es marcador y nombra los picos de enero y la restricción de 2026', () => {
    expect(figure.description).not.toContain('[Texto pendiente');
    expect(figure.description).toContain('723');
    expect(figure.description).toContain('707');
    expect(figure.description).toContain('31 de enero de 2026');
  });
});

describe('contratacion-directa-por-mes (conducta de T2)', () => {
  it('conserva 58 filas y 8 suprimidas', () => {
    const figure = getFigure('contratacion-directa-por-mes');
    expect(figure.rows).toHaveLength(58);
    expect(figure.rows.filter((row) => row.is_suppressed)).toHaveLength(8);
  });
});

describe('concentracion-enero (T7, pantalla 4)', () => {
  const ids = [
    'concentracion-enero-por-numero',
    'concentracion-enero-por-valor',
    'concentracion-enero-sin-interadministrativos',
  ] as const;

  it.each(ids)('%s es responsiva y tiene 5 filas de 2022 a 2026 sin supresión', (id) => {
    const figure = getFigure(id);
    expect(figure.responsive).toBe(true);
    expect(figure.rows.map((row) => row.values.year)).toEqual(['2022', '2023', '2024', '2025', '2026']);
    expect(figure.rows.every((row) => !row.is_suppressed)).toBe(true);
    expect(figure.description).not.toContain('[Texto pendiente');
  });

  it('el papel sale de comparison_windows: elecciones en 2022 y 2026, comparación en el resto', () => {
    const roles = getFigure('concentracion-enero-por-numero').rows.map((row) => row.values.role);
    expect(roles).toEqual(['Elecciones', 'Comparación', 'Comparación', 'Comparación', 'Elecciones']);
  });

  it('la razón de la figura por número es la de indicators.json, sin recalcular', () => {
    const cells = (getIndicators()?.cells ?? []).filter(
      (cell) => cell.indicator === 'I2' && cell.level === 'district' && cell.variant === null && cell.measure === 'count',
    );
    const figure = getFigure('concentracion-enero-por-numero');
    for (const cell of cells) {
      const row = figure.rows.find((candidate) => candidate.values.year === cell.period);
      expect(row?.values.ratio).toBe(cell.ratio);
    }
  });

  it('la descripción por número nombra 58,3 % y 65,3 %; la de valor usa n = 1.136 en 2025', () => {
    expect(getFigure('concentracion-enero-por-numero').description).toContain('58,3');
    expect(getFigure('concentracion-enero-por-numero').description).toContain('65,3');
    const value = getFigure('concentracion-enero-por-valor');
    expect(value.rows.find((row) => row.values.year === '2025')?.values.sample_size).toBe(1136);
  });

  it('el CSV escribe la razón cruda con punto decimal', () => {
    const csv = toCsv(getFigure('concentracion-enero-por-numero'));
    expect(csv).toContain('0.583065');
  });

  it('el CSV de contratacion-directa-por-mes sigue igual (conducta previa)', () => {
    const csv = toCsv(getFigure('contratacion-directa-por-mes'));
    expect(csv.split('\r\n')[1]).toMatch(/^enero de 2022,723,/);
  });
});

describe('objeción (T8, pantalla 5)', () => {
  const byType = getFigure('concentracion-enero-por-tipo');
  const spans = getFigure('contratos-enero-despues-de-la-restriccion');
  const cellOf = (variant: string, period: string) =>
    (getIndicators()?.cells ?? []).find(
      (cell) =>
        cell.indicator === 'I2' && cell.level === 'district' && cell.variant === variant && cell.measure === 'count' && cell.period === period,
    );

  it('por tipo: es responsiva y tiene 10 filas (5 años × 2 tipos)', () => {
    expect(byType.responsive).toBe(true);
    expect(byType.rows).toHaveLength(10);
    expect(new Set(byType.rows.map((row) => row.values.type))).toEqual(new Set(['Prestación de servicios', 'Resto de tipos']));
  });

  it('por tipo: el papel sale de comparison_windows y la razón es la de indicators.json', () => {
    const service2026 = byType.rows.find((row) => row.values.year === '2026' && row.values.type === 'Prestación de servicios');
    expect(service2026?.values.role).toBe('Elecciones');
    expect(service2026?.values.ratio).toBe(cellOf('service_contract', '2026')?.ratio);
    const rest2023 = byType.rows.find((row) => row.values.year === '2023' && row.values.type === 'Resto de tipos');
    expect(rest2023?.values.role).toBe('Comparación');
    expect(rest2023?.values.ratio).toBe(cellOf('non_service_contract', '2023')?.ratio);
  });

  it('por tipo: la descripción nombra 78,6 y 27,1 y no es marcador', () => {
    expect(byType.description).toContain('78,6');
    expect(byType.description).toContain('27,1');
    expect(byType.description).not.toContain('[Texto pendiente');
  });

  it('duración: es responsiva, tiene 5 filas y la razón es la de spans_restriction', () => {
    expect(spans.responsive).toBe(true);
    expect(spans.rows.map((row) => row.values.year)).toEqual(['2022', '2023', '2024', '2025', '2026']);
    for (const row of spans.rows) expect(row.values.ratio).toBe(cellOf('spans_restriction', String(row.values.year))?.ratio);
  });

  it('duración: usa rótulos propios y la descripción nombra 98,9 y la restricción de referencia', () => {
    expect(spans.columns.find((column) => column.key === 'numerator')?.label).toBe('Terminan después de la restricción');
    expect(spans.description).toContain('98,9');
    expect(spans.description).toContain('restricción de referencia');
  });

  it('conducta previa: los rótulos de la figura por número no cambian', () => {
    const labels = getFigure('concentracion-enero-por-numero').columns.map((column) => column.label);
    expect(labels).toContain('Contratos en la ventana');
    expect(labels).toContain('Contratos en total');
  });
});
