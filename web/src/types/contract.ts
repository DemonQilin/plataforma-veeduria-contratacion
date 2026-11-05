// Archivo generado por `pnpm gen:types` desde data/schema/. No lo edites a mano.

export type DenominatorEnd = string;
export type ReferenceRestrictionEnd = string;
export type Role = "treatment" | "control";
export type WindowEnd = string;
export type WindowStart = string;
export type Year = number;
export type ComparisonWindows = ComparisonYear[];
export type Cycle = string;
export type End = string;
export type Scope = "direct_award" | "interadministrative";
/**
 * @minItems 1
 */
export type RestrictionSources = [string, ...string[]];
export type Start = string;
export type Status = "ended" | "ongoing" | "upcoming";
export type Restrictions = ElectoralRestriction[];

/**
 * Restricciones por inicio y ventanas de I2 por año (docs/reglas.md, sección 7).
 */
export interface ElectoralCalendar {
  comparison_windows: ComparisonWindows;
  restrictions: Restrictions;
}
/**
 * La ventana de comparación de I2 de un año (R11, R12).
 */
export interface ComparisonYear {
  denominator_end: DenominatorEnd;
  reference_restriction_end: ReferenceRestrictionEnd;
  role: Role;
  window_end: WindowEnd;
  window_start: WindowStart;
  year: Year;
}
/**
 * Un periodo de la Ley de Garantías con su fuente (R10).
 *
 * `status` es relativo a la fecha de corte (R12): `ended` si ya terminó, `upcoming` si aún no
 * empieza y `ongoing` en cualquier otro caso. Los extremos son inclusivos.
 */
export interface ElectoralRestriction {
  cycle: Cycle;
  end: End;
  scope: Scope;
  sources: RestrictionSources;
  start: Start;
  status: Status;
}

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

export type ContractCount = number;
export type ContractType =
  ("service_contract" | "interadministrative" | "works" | "supply_and_purchase" | "public_credit" | "other") | null;
export type SeriesIsSuppressed = boolean;
export type SeriesPeriod = string;
export type ProcurementMethod =
  | (
      | "direct_award"
      | "special_regime"
      | "public_tender"
      | "abbreviated_selection"
      | "merit_based_selection"
      | "minimum_amount"
      | "other"
    )
  | null;
export type Value = number | null;
export type ValueSampleSize = number;
export type Rows = MonthlySeriesRow[];

/**
 * Una fila por mes, modalidad y tipo del Distrito (docs/reglas.md, sección 7).
 */
export interface MonthlySeries {
  rows: Rows;
}
/**
 * Contratos y valor de un mes, por modalidad y tipo (docs/reglas.md, sección 7; ADR 0040).
 *
 * Una modalidad o un tipo vacíos son el total de esa dimensión. El conteo siempre se publica
 * (es la `n` de R13); el valor se suprime si lo respaldan menos de 5 contratos con valor.
 */
export interface MonthlySeriesRow {
  contract_count: ContractCount;
  contract_type: ContractType;
  is_suppressed: SeriesIsSuppressed;
  period: SeriesPeriod;
  procurement_method: ProcurementMethod;
  value: Value;
  value_sample_size: ValueSampleSize;
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
export type Count = number;
export type Share = number | null;
export type Total = number;
export type UnassignedPeriod = string;
export type Years = UnassignedYear[];
export type Catalog = "procurement_method" | "contract_type" | "supplier_type" | "addition_type" | "department";
export type RawText = string;
export type RowCount = number;
export type UnrecognizedSource = string;
export type UnrecognizedValues = UnrecognizedValue[];

/**
 * Calidad de datos que el tablero advierte (docs/reglas.md, sección 7).
 */
export interface Quality {
  reconciliation: Reconciliation;
  truncated_rows: TruncatedRows;
  unassigned_share: UnassignedShare;
  unrecognized_values: UnrecognizedValues;
  unsigned_records: QualityShare;
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
/**
 * Filas de MEData cortadas en origen, que no traen valores (ADR 0010, ADR 0028, ADR 0042).
 *
 * `rows` son las líneas de MEData · Ejecución; `contracts`, los contratos cuyas líneas vienen
 * todas cortadas.
 */
export interface TruncatedRows {
  contracts: QualityShare;
  rows: QualityShare;
}
/**
 * Cuántos de un total cumplen una condición de calidad, con su proporción (ADR 0042).
 */
export interface QualityShare {
  count: Count;
  share: Share;
  total: Total;
}
/**
 * Contratos «Sin asignar» en el Distrito y por año de firma (R8; ADR 0042).
 */
export interface UnassignedShare {
  district: QualityShare;
  years: Years;
}
/**
 * Contratos sin secretaría de un año de firma (R8).
 */
export interface UnassignedYear {
  period: UnassignedPeriod;
  unassigned: QualityShare;
}
/**
 * Un texto que un catálogo no reconoce, con las filas de la copia que lo traen (R6).
 */
export interface UnrecognizedValue {
  catalog: Catalog;
  raw_text: RawText;
  row_count: RowCount;
  source: UnrecognizedSource;
}
