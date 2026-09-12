import { useQueries } from '@tanstack/react-query'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { ExplorerGrid, ExplorerHeader, MetricSelect } from '../components/Explorer'
import { EmptyState, ErrorState, LoadingState, formatNumber, metricLabels } from '../components/Shared'
import { useExploration } from '../context/ExplorationContext'

export function NestedCvPage() {
  const { state, update, query } = useExploration()
  const [cv, experiments] = useQueries({ queries: [
    { queryKey: ['cv-results'], queryFn: () => api.cvResults() },
    { queryKey: ['experiments'], queryFn: () => api.experiments() },
  ] })
  if (cv.isLoading || experiments.isLoading) return <LoadingState />
  if (cv.isError || experiments.isError) return <ErrorState error={(cv.error || experiments.error) as Error} retry={() => { cv.refetch(); experiments.refetch() }} />
  const available = cv.data ?? []
  const model = available.find(item => item.model_key === state.model) ?? available.find(item => item.model_key === 'custom_random_forest') ?? available[0]
  if (!model) return <EmptyState />
  const selected = model.folds.find(item => item.fold === state.fold) ?? model.folds[0]
  const chart = model.folds.map(item => ({ fold: item.fold, value: item.metrics[state.metric] }))
  const experiment = experiments.data?.find(item => item.slug === model.experiment_slug)

  return <div className="explorer-page"><ExplorerHeader title="Nested CV" description="Външният fold оценява модела; вътрешната 5-fold схема избира параметри само в обучаващата част." />
    <ExplorerGrid controls={<><MetricSelect /><label className="control-field"><span>Модел</span><select value={model.model_key} onChange={event => update({ model: event.target.value })}>{available.map(item => <option key={item.model_key} value={item.model_key}>{item.model}</option>)}</select></label><div className="fold-selector">{model.folds.map(item => <button className={item.fold === selected.fold ? 'active' : ''} key={item.fold} onClick={() => update({ fold: item.fold })}>{item.fold}</button>)}</div></>}
      visualization={<><div className="cv-diagram" aria-label={`Външен fold ${selected.fold} е валидационен`}><div className="outer-folds">{model.folds.map(item => <button onClick={() => update({ fold: item.fold })} key={item.fold} className={item.fold === selected.fold ? 'validation' : 'training'}><span>F{item.fold}</span><small>{item.fold === selected.fold ? 'валидация' : 'обучение'}</small></button>)}</div><div className="inner-boundary"><strong>Вътрешен 5-fold избор</strong><div>{[1,2,3,4,5].map(item => <i key={item}>I{item}</i>)}</div><p>Външният валидационен fold остава извън стандартизацията, LASSO и настройването.</p></div></div><div className="chart-frame"><h2>{metricLabels[state.metric]} по външен fold</h2><ResponsiveContainer width="100%" height={210}><LineChart data={chart}><CartesianGrid stroke="#e2e5e8" vertical={false} /><XAxis dataKey="fold" label={{ value: 'Външен fold', position: 'insideBottom', offset: -2 }} /><YAxis domain={[0, 1]} /><Tooltip /><Line type="linear" dataKey="value" stroke="#5b4bdb" strokeWidth={2} dot={{ fill: '#fff', stroke: '#111318', strokeWidth: 2 }} activeDot={{ fill: '#b8ff1a', r: 6 }} /></LineChart></ResponsiveContainer></div></>}
      details={<><span className="detail-index">F{selected.fold}</span><h2>{model.model}</h2><dl className="compact-dl"><dt>Обучаващи</dt><dd>{selected.training_patient_count ?? 'Няма запис'}</dd><dt>Валидационни</dt><dd>{selected.validation_patient_count ?? 'Няма запис'}</dd><dt>Избрани probe sets</dt><dd>{selected.selected_probe_count ?? 'Няма запис'}</dd><dt>{metricLabels[state.metric]}</dt><dd>{formatNumber(selected.metrics[state.metric])}</dd>{Object.entries(selected.selected_parameters).map(([key,value]) => <><dt key={`${key}-k`}>{key}</dt><dd key={`${key}-v`}>{String(value)}</dd></>)}</dl><p className="evidence-note">Класови разпределения по fold не са записани.</p><Link className="button primary" to={`/process/lasso?${query}&fold=${selected.fold}`}>Отвори селекциите</Link><details className="metadata-drawer"><summary>Метаданни</summary><code>{experiment?.source_path}</code></details></>}
      table={<><div className="table-toolbar"><h2>Fold резултати</h2><div><a className="button secondary" href={api.tableExportUrl('fold-results', { experiment: model.experiment_slug, model: model.model_key, format: 'csv' })}>CSV</a> <a className="button secondary" href={api.tableExportUrl('fold-results', { experiment: model.experiment_slug, model: model.model_key, format: 'xlsx' })}>XLSX</a></div></div><div className="table-scroll"><table><thead><tr><th>Fold</th><th>Избрани</th>{Object.values(metricLabels).map(label => <th key={label}>{label}</th>)}</tr></thead><tbody>{model.folds.map(item => <tr key={item.fold} className={item.fold === selected.fold ? 'selected-row' : ''} onClick={() => update({ fold: item.fold })}><th>{item.fold}</th><td>{item.selected_probe_count ?? '—'}</td>{Object.keys(metricLabels).map(metric => <td key={metric}>{formatNumber(item.metrics[metric as keyof typeof item.metrics])}</td>)}</tr>)}</tbody></table></div></>}
    /></div>
}
