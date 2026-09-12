import { useMemo, useState } from 'react'
import { useQueries, useQuery } from '@tanstack/react-query'
import { api } from '../api'
import { EmptyState, ErrorState, LoadingState, formatNumber, metricLabels } from '../components/Shared'
import { useExploration } from '../context/ExplorationContext'

const tabs = ['Настройки', 'Fold резултати', 'Характеристики', 'Предикции', 'Метаданни'] as const

export function ExperimentsPage() {
  const { state, update } = useExploration()
  const [dataset, setDataset] = useState('')
  const [stage, setStage] = useState('')
  const [tab, setTab] = useState<(typeof tabs)[number]>('Настройки')
  const [experiments, cv] = useQueries({ queries: [
    { queryKey: ['experiments'], queryFn: () => api.experiments() },
    { queryKey: ['cv-results'], queryFn: () => api.cvResults() },
  ] })
  const visible = useMemo(() => (experiments.data ?? []).filter(item => (!dataset || item.dataset === dataset) && (!stage || item.evaluation_stage === stage)), [experiments.data, dataset, stage])
  const selected = visible.find(item => item.slug === state.experiment) ?? visible[0]
  const selectedRun = selected?.models.find(item => item.model_key === state.model) ?? selected?.models[0]
  const features = useQuery({ queryKey: ['experiment-features', selected?.slug], queryFn: () => api.features({ experiment: selected!.slug, limit: 20 }), enabled: Boolean(selected && tab === 'Характеристики') })
  const predictions = useQuery({ queryKey: ['experiment-predictions', selected?.slug, selectedRun?.model_key], queryFn: () => api.predictions({ experiment: selected!.slug, model: selectedRun?.model_key, limit: 20 }), enabled: Boolean(selected && selectedRun && tab === 'Предикции') })
  if (experiments.isLoading || cv.isLoading) return <LoadingState />
  if (experiments.isError || cv.isError) return <ErrorState error={(experiments.error || cv.error) as Error} retry={() => { experiments.refetch(); cv.refetch() }} />
  const foldRecord = cv.data?.find(item => item.experiment_slug === selected?.slug && item.model_key === selectedRun?.model_key)

  return <div className="workspace-page dense-results"><header className="compact-page-header"><div><span className="section-code">RESEARCH RESULTS</span><h1>Експерименти</h1><p>Филтриране на завършените изпълнения и проверка на настройките, fold резултатите и свързаните записи.</p></div></header>
    <div className="filters compact"><label>Набор<select value={dataset} onChange={event => setDataset(event.target.value)}><option value="">Всички</option><option>GSE25055</option><option>GSE25065</option></select></label><label>Етап<select value={stage} onChange={event => setStage(event.target.value)}><option value="">Всички</option><option value="cross_validation">Кръстосана валидация</option><option value="final_training">Финален fit</option><option value="external_validation">Външна валидация</option></select></label><span className="filter-summary">{visible.length} експеримента</span></div>
    <div className="master-detail"><section className="master-table"><table><thead><tr><th>Експеримент</th><th>Набор</th><th>Модели</th><th>Статус</th></tr></thead><tbody>{visible.map(item => <tr key={item.slug} className={item.slug === selected?.slug ? 'selected-row' : ''} onClick={() => update({ experiment: item.slug, dataset: item.dataset })}><th>{item.name}</th><td><code>{item.dataset}</code></td><td>{item.models.length}</td><td>{item.locked ? 'Заключен' : 'Завършен'}</td></tr>)}</tbody></table></section>
      <aside className="run-detail">{selected && selectedRun ? <><span className="detail-index">ИЗБРАН МОДЕЛ</span><h2>{selectedRun.display_name}</h2><label className="control-field"><span>Модел</span><select value={selectedRun.model_key} onChange={event => update({ model: event.target.value })}>{selected.models.map(item => <option key={item.model_key} value={item.model_key}>{item.display_name}</option>)}</select></label><div className="run-metrics">{Object.entries(selectedRun.overall_metrics).slice(0,4).map(([key,value]) => <span key={key}><small>{metricLabels[key] ?? key}</small><b>{formatNumber(value)}</b></span>)}</div></> : <EmptyState />}</aside>
    </div>
    {selected && selectedRun && <section className="detail-tabs"><div className="tab-bar">{tabs.map(item => <button key={item} className={tab === item ? 'active' : ''} onClick={() => setTab(item)}>{item}</button>)}</div><div className="tab-content">
      {tab === 'Настройки' && <div className="configuration-grid">{Object.entries(selectedRun.configuration).map(([key,value]) => <span key={key}><small>{key.replaceAll('_',' ')}</small><code>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</code></span>)}</div>}
      {tab === 'Fold резултати' && (foldRecord ? <><div className="table-toolbar"><b>{foldRecord.model}</b><div><a className="button secondary" href={api.tableExportUrl('fold-results', { experiment: selected.slug, model: selectedRun.model_key, format: 'csv' })}>CSV</a> <a className="button secondary" href={api.tableExportUrl('fold-results', { experiment: selected.slug, model: selectedRun.model_key, format: 'xlsx' })}>XLSX</a></div></div><table><thead><tr><th>Fold</th><th>Train</th><th>Validation</th><th>Probe sets</th><th>ROC-AUC</th><th>PR-AUC</th><th>F1</th></tr></thead><tbody>{foldRecord.folds.map(item => <tr key={item.fold}><th>{item.fold}</th><td>{item.training_patient_count}</td><td>{item.validation_patient_count}</td><td>{item.selected_probe_count}</td><td>{formatNumber(item.metrics.roc_auc)}</td><td>{formatNumber(item.metrics.pr_auc)}</td><td>{formatNumber(item.metrics.f1)}</td></tr>)}</tbody></table></> : <EmptyState />)}
      {tab === 'Характеристики' && (features.isLoading ? <LoadingState /> : features.data?.items.length ? <><div className="table-toolbar"><b>{features.data.total} записа</b><a className="button secondary" href={api.tableExportUrl('features', { experiment: selected.slug, format: 'csv' })}>CSV</a></div><table><thead><tr><th>Probe ID</th><th>Ген</th><th>Fold</th><th>Коефициент</th></tr></thead><tbody>{features.data.items.map(item => <tr key={`${item.probe_id}-${item.fold}`}><th><code>{item.probe_id}</code></th><td>{item.annotation.gene_symbol || '—'}</td><td>{item.fold ?? '—'}</td><td>{formatNumber(item.coefficient,5)}</td></tr>)}</tbody></table></> : <EmptyState />)}
      {tab === 'Предикции' && (predictions.isLoading ? <LoadingState /> : predictions.data?.items.length ? <><div className="table-toolbar"><b>{predictions.data.total} записа</b><a className="button secondary" href={api.tableExportUrl('predictions', { experiment: selected.slug, model: selectedRun.model_key, format: 'csv' })}>CSV</a></div><table><thead><tr><th>Проба</th><th>Реален</th><th>Прогноза</th><th>Вероятност</th><th>Fold</th></tr></thead><tbody>{predictions.data.items.map(item => <tr key={item.patient_id}><th><code>{item.patient_id}</code></th><td>{item.actual_class}</td><td>{item.predicted_class}</td><td>{formatNumber(item.probability)}</td><td>{item.validation_fold ?? '—'}</td></tr>)}</tbody></table></> : <EmptyState />)}
      {tab === 'Метаданни' && <dl className="metadata-list"><dt>Експеримент</dt><dd><code>{selected.slug}</code></dd><dt>Етап</dt><dd>{selected.evaluation_stage}</dd><dt>Обхват</dt><dd>{selected.result_scope}</dd><dt>Създаден</dt><dd>{selected.created_at ? new Date(selected.created_at).toLocaleString('bg-BG') : 'Няма запис'}</dd><dt>Артефакт</dt><dd><code>{selected.source_path}</code></dd></dl>}
    </div></section>}
  </div>
}
