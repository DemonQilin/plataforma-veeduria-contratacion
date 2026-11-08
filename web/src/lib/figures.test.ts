// T5 (S7, pantalla 2): la figura de periodos de restricción solo presenta celdas de
// electoral_calendar.json; la de T2 sigue igual (S6).
import { describe, expect, it } from 'vitest';
import { getFigure } from './figures';

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
    expect(figure.rows.every((row) => !row.suppressed)).toBe(true);
  });

  it('la descripción en texto menciona la fecha de corte y no es un marcador', () => {
    expect(figure.description).toContain('30 de octubre de 2026');
    expect(figure.description).not.toContain('[Texto pendiente');
  });
});

describe('contratacion-directa-por-mes (conducta de T2)', () => {
  it('conserva 58 filas y 8 suprimidas', () => {
    const figure = getFigure('contratacion-directa-por-mes');
    expect(figure.rows).toHaveLength(58);
    expect(figure.rows.filter((row) => row.suppressed)).toHaveLength(8);
  });
});
