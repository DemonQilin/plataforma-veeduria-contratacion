// CSV de una figura (docs/adr/0048): UTF-8 con BOM, comas y punto decimal.
// La celda suprimida sale vacía y la columna `suprimida` lo indica.
import type { FigureSpec } from './figures';

const escape = (text: string): string =>
  /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;

export function toCsv(figure: FigureSpec): string {
  const header = [...figure.columns.map((column) => column.label), 'suprimida'];
  const lines = figure.rows.map((row) =>
    [
      ...figure.columns.map((column) => {
        const cell = row.values[column.key] ?? null;
        return column.suppressible && row.is_suppressed ? '' : escape(cell === null ? '' : String(cell));
      }),
      row.is_suppressed ? 'sí' : 'no',
    ].join(','),
  );
  return `﻿${[header.map(escape).join(','), ...lines].join('\r\n')}\r\n`;
}
