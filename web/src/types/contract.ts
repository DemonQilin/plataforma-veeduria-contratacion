// Archivo generado por `pnpm gen:types` desde data/schema/. No lo edites a mano.

export type CutoffDate = string;
export type RulesVersion = string;
export type License = string;
export type Name = string;
export type Url = string;
export type Sources = Source[];

/**
 * Fecha de corte, fuentes con enlace y licencia, y versión de las reglas.
 */
export interface Metadata {
  cutoff_date: CutoffDate;
  rules_version: RulesVersion;
  sources: Sources;
}
export interface Source {
  license: License;
  name: Name;
  url: Url;
}
