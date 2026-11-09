// R8: todo código de secretaría de las salidas tiene etiqueta (ADR 0053).
import { describe, expect, it } from 'vitest';
import { getIndicators } from './data';
import { DEPARTMENT_LABELS, departmentLabel } from './departments';

describe('DEPARTMENT_LABELS', () => {
  it('cubre cada secretaría de indicators.json', () => {
    const codes = new Set(
      (getIndicators()?.cells ?? []).flatMap((cell) => (cell.department ? [cell.department] : [])),
    );
    expect(codes.size).toBeGreaterThan(0);
    expect([...codes].filter((code) => !(code in DEPARTMENT_LABELS))).toEqual([]);
  });

  it('devuelve el código cuando no hay etiqueta', () => {
    expect(departmentLabel('health')).toBe('Salud');
    expect(departmentLabel('desconocida')).toBe('desconocida');
  });
});
