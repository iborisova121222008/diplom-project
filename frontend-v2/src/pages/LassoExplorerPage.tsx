import { useEffect, useState } from 'react'
import { useQueries, useQuery } from '@tanstack/react-query'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api'
import { ChartExportActions } from '../components/ChartExport'
import { ExplorerGrid, ExplorerHeader } from '../components/Explorer'
import { EmptyState, ErrorState, LoadingState, formatNumber } from '../components/Shared'
import { useExploration } from '../context/ExplorationContext'

export function LassoExplorerPage() {
  const { state, update } = useExploration()
  const [search, setSearch] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  useEffect(() => {
    const timer = window.setTimeout(() => setSearchQuery(search), 250)
    return () => window.clearTimeout(timer)
  }, [search])
  const [datasets, cv, frequency, similarities, finalFeatures] = useQueries({ queries: [
    { queryKey: ['datasets'], queryFn: api.datasets },
    { queryKey: ['cv-results', 'lasso'], queryFn: () => api.cvResults('lasso_logistic') },
    { queryKey: ['feature-frequency'], queryFn: api.featureFrequency },
    { queryKey: ['similarities'], queryFn: api.similarities },
    { queryKey: ['final-features'], queryFn: () => api.features({ experiment: 'final-model-gse25055', offset: 0, limit: 100, sort_by: 'probe_id' }) },
  ] })
  const heatmap = useQuery({ queryKey: ['feature-heatmap', state.topN, state.minimumFrequency, searchQuery], queryFn: () => api.featureHeatmap(state.topN, state.minimumFrequency, searchQuery) })
  const loading = [datasets, cv, frequency, similarities, finalFeatures, heatmap].some(item => item.isLoading)
  if (loading) return <LoadingState />
  const failed = [datasets, cv, frequency, similarities, finalFeatures, heatmap].find(item => item.isError)
  if (failed) return <ErrorState error={failed.error} retry={() => { datasets.refetch(); cv.refetch(); frequency.refetch(); similarities.refetch(); finalFeatures.refetch(); heatmap.refetch() }} />

  const lasso = cv.data?.[0]
  const selectedFold = lasso?.folds.find(item => item.fold === state.fold)
  const finalRows = finalFeatures.data?.items ?? []
  const distinctCount = frequency.data?.reduce((sum, item) => sum + item.probe_count, 0) ?? 0
  const remainingCount = frequency.data?.filter(item => item.selected_folds >= state.minimumFrequency).reduce((sum, item) => sum + item.probe_count, 0) ?? 0
  const matrix = (() => {
    const lookup = new Map((similarities.data ?? []).flatMap(item => [[`${item.fold_a}-${item.fold_b}`, item], [`${item.fold_b}-${item.fold_a}`, item]]))
    return Array.from({ length: 10 }, (_, row) => Array.from({ length: 10 }, (_, column) => row === column ? null : lookup.get(`${row + 1}-${column + 1}`)))
  })()
  const selectedFeature = finalRows.find(item => item.probe_id === state.probe) ?? finalRows[0]

  return <div className="explorer-page"><ExplorerHeader title="LASSO и стабилност" description="Реални fold селекции, честота, припокриване и коефициенти от заключения 15-probe модел." />
    <ExplorerGrid controls={<><label className="control-field"><span>Външен fold</span><select value={state.fold} onChange={event => update({ fold: Number(event.target.value) })}>{Array.from({ length: 10 }, (_, index) => <option key={index + 1} value={index + 1}>Fold {index + 1}</option>)}</select></label><label className="control-field"><span>Минимална честота: {state.minimumFrequency}/10</span><input type="range" min="1" max="10" value={state.minimumFrequency} onChange={event => update({ minimumFrequency: Number(event.target.value) })} /><b>{remainingCount.toLocaleString('bg-BG')} probe sets</b></label><label className="control-field"><span>Редове в картата</span><select value={state.topN} onChange={event => update({ topN: Number(event.target.value) })}><option value="25">25</option><option value="30">30</option><option value="40">40</option></select></label><label className="control-field"><span>Probe или ген</span><input value={search} onChange={event => setSearch(event.target.value)} placeholder="напр. HMGXB3" /></label></>}
      visualization={<><div className="reduction-branches"><div className="branch-origin"><b>{datasets.data?.[0]?.feature_count.toLocaleString('bg-BG')}</b><span>измерени probe sets</span></div><div className="branch-lines"><section><small>АНАЛИЗ ПО FOLD</small><div className="reduction-flow"><span className="active"><b>{selectedFold?.selected_probe_count ?? '—'}</b>Fold {state.fold} селекция</span><i>→</i><span><b>{distinctCount.toLocaleString('bg-BG')}</b>различни, избрани ≥1 fold</span><i>→</i><span className="separate"><b>72</b>stability-filtered аналитичен subset</span></div></section><section><small>ОТДЕЛЕН ФИНАЛЕН FIT</small><div className="reduction-flow"><span><b>пълен GSE25055</b>нов LASSO fit · C=0.03</span><i>→</i><span className="final"><b>{finalRows.length}</b>подредени финални probes</span></div></section></div></div>
        <div className="lasso-panels"><section className="chart-frame"><h2>Разпределение на честотата</h2><ResponsiveContainer width="100%" height={190}><BarChart data={frequency.data}><CartesianGrid stroke="#e2e5e8" vertical={false} /><XAxis dataKey="selected_folds" label={{ value: 'Избрани fold-ове', position: 'insideBottom', offset: -2 }} /><YAxis /><Tooltip /><Bar dataKey="probe_count" name="Probe sets" fill="#5b4bdb" /></BarChart></ResponsiveContainer></section><section className="heatmap-frame"><h2>Fold × характеристика</h2>{heatmap.data?.length ? <div className="feature-heatmap"><div className="heatmap-row head"><span>Probe / ген</span>{Array.from({ length: 10 }, (_, index) => <b key={index}>F{index + 1}</b>)}</div>{heatmap.data.map(row => <button key={row.probe_id} className={`heatmap-row ${state.probe === row.probe_id ? 'selected' : ''}`} onClick={() => update({ probe: row.probe_id })}><span><code>{row.probe_id}</code><small>{row.gene_symbol || 'без анотация'}</small></span>{Array.from({ length: 10 }, (_, index) => <i key={index} className={row.selected_folds.includes(index + 1) ? 'on' : ''} title={`Fold ${index + 1}: ${row.selected_folds.includes(index + 1) ? 'избрана' : 'не е избрана'}`} />)}</button>)}</div> : <EmptyState />}</section></div>
        <section className="jaccard-panel"><div><h2>Jaccard матрица</h2><p>45 съхранени двойки; диагоналът е идентичност.</p></div><div className="jaccard-matrix">{matrix.flatMap((row, r) => row.map((item, c) => <button key={`${r}-${c}`} className={`${r === c ? 'diagonal' : ''} ${r + 1 === state.fold || c + 1 === state.fold ? 'highlight' : ''}`} onClick={() => update({ fold: r + 1 })} title={item ? `F${r + 1}/F${c + 1}: ${item.shared_probes} общи, ${item.union_probes} обединение` : `F${r + 1}: 1.000`}>{r === c ? '1' : formatNumber(item?.jaccard_similarity, 2)}</button>))}</div></section></>}
      details={<>{selectedFeature ? <><span className="detail-index">PROBE</span><h2><code>{selectedFeature.probe_id}</code></h2><p>{selectedFeature.annotation.gene_symbol || 'Без gene symbol'} · {selectedFeature.annotation.gene_name || 'Без gene name'}</p><dl className="compact-dl"><dt>Коефициент</dt><dd>{formatNumber(selectedFeature.coefficient, 5)}</dd><dt>Посока</dt><dd>{(selectedFeature.coefficient ?? 0) >= 0 ? 'Свързан с pCR прогноза' : 'Свързан с RD прогноза'}</dd><dt>Картографиране</dt><dd>{selectedFeature.annotation.mapping_status}</dd></dl></> : <EmptyState />}<p className="evidence-note">LASSO е L1-регуляризиран логистичен модел. Ненулевите коефициенти определят fold-local набора; корелирани probes могат да се редуват. Селекцията не доказва причинност.</p></>}
      table={<><div className="table-toolbar"><h2>Финални коефициенти</h2><div><ChartExportActions targetId="final-coefficient-chart" filename="final-lasso-coefficients" /> <a className="button secondary" href={api.tableExportUrl('features', { experiment: 'final-model-gse25055', format: 'csv' })}>CSV</a> <a className="button secondary" href={api.tableExportUrl('features', { experiment: 'final-model-gse25055', format: 'xlsx' })}>XLSX</a></div></div><div className="coeff-workspace"><div id="final-coefficient-chart"><ResponsiveContainer width="100%" height={310}><BarChart data={finalRows} layout="vertical" margin={{ left: 22 }}><CartesianGrid stroke="#e2e5e8" horizontal={false} /><XAxis type="number" /><YAxis type="category" dataKey="probe_id" width={105} tick={{ fontFamily: 'monospace', fontSize: 10 }} /><Tooltip /><Bar dataKey="coefficient" name="Коефициент">{finalRows.map(item => <Cell key={item.probe_id} fill={(item.coefficient ?? 0) >= 0 ? '#16867a' : '#d45b50'} />)}</Bar></BarChart></ResponsiveContainer></div><div className="table-scroll"><table><thead><tr><th>Probe ID</th><th>Ген</th><th>Коефициент</th><th>Асоциация</th></tr></thead><tbody>{finalRows.map(item => <tr key={item.probe_id} className={item.probe_id === selectedFeature?.probe_id ? 'selected-row' : ''} onClick={() => update({ probe: item.probe_id })}><th><code>{item.probe_id}</code></th><td>{item.annotation.gene_symbol || '—'}</td><td>{formatNumber(item.coefficient, 5)}</td><td>{(item.coefficient ?? 0) >= 0 ? 'pCR' : 'RD'}</td></tr>)}</tbody></table></div></div></>}
    /></div>
}
