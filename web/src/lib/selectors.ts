// Elige celdas de data/outputs/. No calcula ni filtra por reglas de negocio
// (regla 2 de CLAUDE.md); T3 completa los selectores de las demás pantallas.
import { getMonthlySeries } from './data';

/** Contratación directa por mes, todos los tipos de contrato (celdas sin `contract_type`). */
export function directAwardMonthly() {
  return (getMonthlySeries()?.rows ?? []).filter(
    (row) => row.procurement_method === 'direct_award' && row.contract_type === null,
  );
}
