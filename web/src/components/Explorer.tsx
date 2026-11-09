// Isla del explorador (pantalla 6, ADR 0053). Solo muestra lo que arma lib/explorer.ts:
// no calcula ni formatea cifras (regla 2 de CLAUDE.md).
import { useState } from 'react';
import type { ExplorerData, ExplorerRow } from '../lib/explorer';
import './explorer.css';

interface Props {
  data: ExplorerData;
}

function Bars({ caption, rows, selected }: { caption: string; rows: readonly ExplorerRow[]; selected?: string | null }) {
  return (
    <table className="xp-bars">
      <caption className="visually-hidden">{caption}</caption>
      <thead className="visually-hidden">
        <tr>
          <th scope="col">Nombre</th>
          <th scope="col">Cifra y base</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.code ?? 'district'} className={row.code === selected ? 'xp-selected' : undefined}>
            <th scope="row">{row.label}</th>
            <td>
              <span className="xp-track">
                <span
                  className={`xp-bar ${row.code === null ? 'xp-bar--district' : ''}`}
                  aria-hidden="true"
                  style={{ width: `${row.width}%` }}
                />
                <b className="xp-val">{row.display}</b>
              </span>
              <span className="xp-note">{row.note}</span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function Explorer({ data }: Props) {
  const [indicatorId, setIndicatorId] = useState(data.indicators[0]?.id ?? 'I1');
  const indicator = data.indicators.find((item) => item.id === indicatorId) ?? data.indicators[0];
  const [selectedPeriod, setSelectedPeriod] = useState(indicator?.periods.at(-1)?.period ?? '');
  const [department, setDepartment] = useState('');
  if (!indicator) return null;

  const current = indicator.periods.find((item) => item.period === selectedPeriod) ?? indicator.periods.at(-1);
  if (!current) return null;

  // Las secretarías se listan por el orden de la lista más reciente del indicador.
  const options = (indicator.periods.at(-1)?.departments ?? []).filter((row) => row.code);
  const yearly = department
    ? indicator.periods.flatMap((item) => {
        const row = item.departments.find((candidate) => candidate.code === department);
        return row ? [{ ...row, code: item.period, label: item.period }] : [];
      })
    : [];
  const selected = current.departments.find((row) => row.code === department);

  const changeIndicator = (id: string) => {
    const next = data.indicators.find((item) => item.id === id);
    if (!next) return;
    setIndicatorId(next.id);
    if (!next.periods.some((item) => item.period === selectedPeriod)) setSelectedPeriod(next.periods.at(-1)?.period ?? '');
  };

  return (
    <div className="xp">
      <form className="xp-controls" onSubmit={(event) => event.preventDefault()}>
        <label>
          Indicador
          <select value={indicator.id} onChange={(event) => changeIndicator(event.target.value)}>
            {data.indicators.map((item) => (
              <option key={item.id} value={item.id}>
                {item.title}
              </option>
            ))}
          </select>
        </label>
        <label>
          Año
          <select value={current.period} onChange={(event) => setSelectedPeriod(event.target.value)}>
            {indicator.periods.map((item) => (
              <option key={item.period} value={item.period}>
                {item.period}
              </option>
            ))}
          </select>
        </label>
        <label>
          Secretaría
          <select value={department} onChange={(event) => setDepartment(event.target.value)}>
            <option value="">Todas</option>
            {options.map((row) => (
              <option key={row.code} value={row.code ?? ''}>
                {row.label}
              </option>
            ))}
          </select>
        </label>
      </form>

      <p className="xp-question" aria-live="polite">
        {indicator.question} · {current.period}
        {selected && <> · {selected.label}: <b>{selected.display}</b> ({selected.note})</>}
      </p>

      <h3>Ranking de secretarías, {current.period}</h3>
      {current.district && (
        <Bars caption={`Referencia del Distrito, ${current.period}`} rows={[current.district]} />
      )}
      <Bars
        caption={`${indicator.title}: secretarías de mayor a menor, ${current.period}`}
        rows={current.departments}
        selected={department || null}
      />

      {yearly.length > 0 && (
        <>
          <h3>Año por año: {selected?.label ?? options.find((row) => row.code === department)?.label}</h3>
          <Bars caption={`${indicator.title} por año en la secretaría elegida`} rows={yearly} />
        </>
      )}
    </div>
  );
}
