// Único módulo que da formato a números y fechas (es-CO).
const number = new Intl.NumberFormat('es-CO');
const percent = new Intl.NumberFormat('es-CO', { style: 'percent', maximumFractionDigits: 1 });
const date = new Intl.DateTimeFormat('es-CO', { dateStyle: 'long', timeZone: 'UTC' });

export const formatNumber = (value: number): string => number.format(value);

export const formatPercent = (ratio: number): string => percent.format(ratio);

/** Recibe una fecha ISO (AAAA-MM-DD) y la muestra en español. */
export const formatDate = (iso: string): string => date.format(new Date(`${iso}T00:00:00Z`));