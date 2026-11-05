// Único archivo que importa desde ../data/outputs (docs/adr/0004).
// El resto del sitio usa las funciones que exporta.
import type { Metadata, MonthlySeries, Quality } from '../types/contract';

const outputs = import.meta.glob<unknown>('../../../data/outputs/*.json', {
  eager: true,
  import: 'default',
});

const read = <T>(name: string): T | undefined =>
  outputs[`../../../data/outputs/${name}.json`] as T | undefined;

export const getMetadata = (): Metadata | undefined => read<Metadata>('metadata');

export const getMonthlySeries = (): MonthlySeries | undefined =>
  read<MonthlySeries>('monthly_series');

export const getQuality =(): Quality | undefined => read<Quality>('quality');