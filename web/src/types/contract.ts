// Archivo generado por `pnpm gen:types` desde data/schema/. No lo edites a mano.

export type Denominator = number | null;
export type Department = string | null;
export type Indicator = "I1" | "I2" | "I3" | "I4" | "I5" | "I6" | "I7" | "I8";
export type IsSuppressed = boolean;
export type Level = "district" | "department";
export type Measure = "count" | "value";
export type Numerator = number | null;
export type Period = string;
export type Ratio = number | null;
export type SampleSize = number;
export type Variant = string | null;
export type Cells = IndicatorCell[];

/**
 * Una fila por indicador, nivel y periodo (docs/reglas.md, sección 7).
 */
export interface Indicators {
  cells: Cells;
}
/**
 * Un indicador en un nivel y un periodo, con su trazabilidad (R16).
 *
 * Una celda suprimida (R13) publica su `sample_size` y oculta numerador, denominador y razón.
 */
export interface IndicatorCell {
  denominator: Denominator;
  department: Department;
  indicator: Indicator;
  is_suppressed: IsSuppressed;
  level: Level;
  measure: Measure;
  numerator: Numerator;
  period: Period;
  ratio: Ratio;
  sample_size: SampleSize;
  variant: Variant;
}

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

export type BelowThreshold = boolean;
export type MedataCount = number;
export type MedataCoverage = number | null;
export type ReconciliationPeriod = string;
export type SecopCount = number;
export type SecopCoverage = number | null;
export type SharedCount = number;
export type SharedShare = number | null;
export type UnionCount = number;
export type Months = ReconciliationMonth[];
export type Threshold = number;

/**
 * Calidad de datos que el tablero advierte (docs/reglas.md, sección 7).
 */
export interface Quality {
  reconciliation: Reconciliation;
}
/**
 * Conciliación mensual y el umbral con el que se advierte (R15).
 */
export interface Reconciliation {
  months: Months;
  threshold: Threshold;
}
/**
 * Un mes de la conciliación SECOP–MEData (R15; ADR 0031).
 *
 * Publica los conteos junto a las razones: con pocos contratos, uno de diferencia mueve mucho
 * el porcentaje y el tablero debe mostrar la base (ADR 0038).
 */
export interface ReconciliationMonth {
  below_threshold: BelowThreshold;
  medata_count: MedataCount;
  medata_coverage: MedataCoverage;
  period: ReconciliationPeriod;
  secop_count: SecopCount;
  secop_coverage: SecopCoverage;
  shared_count: SharedCount;
  shared_share: SharedShare;
  union_count: UnionCount;
}
