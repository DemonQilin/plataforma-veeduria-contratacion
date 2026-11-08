import type { APIRoute, GetStaticPaths } from 'astro';
import { toCsv } from '../../lib/csv';
import { FIGURES, getFigure } from '../../lib/figures';

export const getStaticPaths = (() =>
  FIGURES.map((figure) => ({ params: { figure: figure.id } }))) satisfies GetStaticPaths;

export const GET: APIRoute = ({ params }) =>
  new Response(toCsv(getFigure(params['figure'] ?? '')), {
    headers: { 'Content-Type': 'text/csv; charset=utf-8' },
  });
