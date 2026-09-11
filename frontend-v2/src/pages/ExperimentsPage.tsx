import { useMemo, useState } from 'react'
import { useQueries, useQuery } from '@tanstack/react-query'
import { ChevronRight, LockKeyhole } from 'lucide-react'
import { api } from '../api'
import { CurveChart, MetricComparisonChart } from '../components/Charts'
import { EmptyState, ErrorState, LoadingState, PageHeader, SourceNote, formatNumber, metricLabels } from '../components/Shared'
import type { Experiment } from '../types'

function ExperimentDetails({ experiment }: { experiment: Experiment }) {
  const cv = useQuery({ queryKey: ['cv-results'], queryFn: () => api.cvResults() })
  const curves = useQuery({
    queryKey: ['curves', experiment.slug],
    queryFn: () => api.curves(experiment.slug),
    enabled: experiment.evaluation_stage === 'cross_validation',
  })
  const records = cv.data?.filter(item => item.experiment_slug === experiment.slug) ?? []
  return <section className="panel details-panel">
    <div className="section-heading"><div><p className="section-kicker">Детайли на експеримента</p><h2>{experiment.name}</h2></div>{experiment.locked && <span className="badge locked"><LockKeyhole size={14} /> Заключен</span>}</div>
    <div className="detail-grid"><dl><dt>Набор</dt><dd>{experiment.dataset}</dd><dt>Етап</dt><dd>{experiment.evaluation_stage}</dd><dt>Обхват</dt><dd>{experiment.result_scope}</dd><dt>Време</dt><dd>{experiment.created_at ? new Date(experiment.created_at).toLocaleString('bg-BG') : 'Няма записана информация'}</dd></dl>
      <div><h3>Модели и настройки</h3>{experiment.models.map(model => <details key={model.model_key}><summary>{model.display_name}</summary><div className="configuration-list">{Object.entries(model.configuration).map(([key, value]) => <p key={key}><span>{key.replaceAll('_', ' ')}</span><strong>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</strong></p>)}</div></details>)}</div></div>
    {records.map(record => <div key={record.model_key} className="cv-model-section"><h3>Кръстосана валидация по fold — {record.model}</h3><div className="table-scroll"><table><thead><tr><th>Fold</th><th>Обучаващи</th><th>Валидационни</th><th>Избрани probe sets</th><th>ROC-AUC</th><th>PR-AUC</th><th>F1</th><th>Избрани параметри</th></tr></thead><tbody>{record.folds.map(fold => <tr key={fold.fold}><td>{fold.fold}</td><td>{fold.training_patient_count ?? '—'}</td><td>{fold.validation_patient_count ?? '—'}</td><td>{fold.selected_probe_count ?? '—'}</td><td>{formatNumber(fold.metrics.roc_auc)}</td><td>{formatNumber(fold.metrics.pr_auc)}</td><td>{formatNumber(fold.metrics.f1)}</td><td>{Object.keys(fold.selected_parameters).length ? JSON.stringify(fold.selected_parameters) : 'Няма записана информация'}</td></tr>)}</tbody></table></div>
      <h3>Средни стойности и стандартно отклонение</h3><div className="summary-grid">{Object.entries(record.summary.metrics).map(([key, values]) => <div key={key}><small>{metricLabels[key] ?? key}</small><strong>{formatNumber(values.mean)}</strong><span>± {formatNumber(values.std)}</span></div>)}</div><SourceNote paths={[record.folds[0]?.source_path, record.summary.source_path]} /></div>)}
    {curves.isLoading && <LoadingState label="Подготовка на OOF кривите…" />}
    {curves.data && <div className="two-charts"><CurveChart models={curves.data.models} kind="roc" /><CurveChart models={curves.data.models} kind="precision_recall" /></div>}
    <details className="technical"><summary>Технически детайли</summary><pre>{JSON.stringify(experiment, null, 2)}</pre></details>
    <SourceNote paths={[experiment.source_path, ...experiment.models.map(model => model.configuration_source_path)]} />
  </section>
}

export function ExperimentsPage() {
  const [dataset, setDataset] = useState('')
  const [stage, setStage] = useState('')
  const [model, setModel] = useState('')
  const [status, setStatus] = useState('')
  const [selected, setSelected] = useState('')
  const [experiments, comparison] = useQueries({ queries: [
    { queryKey: ['experiments'], queryFn: () => api.experiments() },
    { queryKey: ['comparison'], queryFn: api.comparison },
  ] })
  const visible = useMemo(() => (experiments.data ?? []).filter(item =>
    (!dataset || item.dataset === dataset)
    && (!stage || item.evaluation_stage === stage)
    && (!model || item.models.some(run => run.model_key === model))
    && (!status || item.status === status)
  ), [dataset, stage, model, status, experiments.data])

  if (experiments.isLoading || comparison.isLoading) return <LoadingState />
  if (experiments.isError || comparison.isError) return <ErrorState error={(experiments.error || comparison.error) as Error} retry={() => { experiments.refetch(); comparison.refetch() }} />
  const selectedExperiment = experiments.data?.find(item => item.slug === selected)

  return <div className="page">
    <PageHeader eyebrow="Завършени изпълнения" title="Експерименти" description="Филтриране, проследяване и сравнение на вече записаните експерименти. Оттук не може да се стартира обучение." />
    <section className="panel"><div className="filters">
      <label>Набор<select value={dataset} onChange={event => setDataset(event.target.value)}><option value="">Всички</option><option>GSE25055</option><option>GSE25065</option></select></label>
      <label>Тип<select value={stage} onChange={event => setStage(event.target.value)}><option value="">Всички</option><option value="cross_validation">Кръстосана валидация</option><option value="final_training">Финално обучение</option><option value="external_validation">Външна валидация</option></select></label>
      <label>Модел<select value={model} onChange={event => setModel(event.target.value)}><option value="">Всички</option><option value="l2_logistic">L2 Logistic</option><option value="lasso_logistic">LASSO</option><option value="custom_random_forest">Custom Random Forest</option><option value="sklearn_random_forest">Sklearn Random Forest</option></select></label>
      <label>Статус<select value={status} onChange={event => setStatus(event.target.value)}><option value="">Всички</option><option value="completed">Завършен</option><option value="locked">Заключен</option></select></label>
    </div>
    {!visible.length ? <EmptyState text="Няма експерименти, които отговарят на филтрите." /> : <div className="table-scroll"><table><thead><tr><th>Експеримент</th><th>Набор</th><th>Етап</th><th>Модели</th><th>Статус</th><th><span className="sr-only">Детайли</span></th></tr></thead><tbody>{visible.map(item => <tr key={item.slug} className={selected === item.slug ? 'selected-row' : ''}><th>{item.name}</th><td>{item.dataset}</td><td>{item.evaluation_stage}</td><td>{item.models.map(run => run.display_name).join(', ') || '—'}</td><td><span className={`badge ${item.locked ? 'locked' : ''}`}>{item.locked ? 'Заключен' : 'Завършен'}</span></td><td><button className="table-action" onClick={() => setSelected(item.slug)} aria-label={`Отвори ${item.name}`}><ChevronRight size={17} /></button></td></tr>)}</tbody></table></div>}
    <SourceNote paths={visible.map(item => item.source_path)} /></section>
    {selectedExperiment && <ExperimentDetails experiment={selectedExperiment} />}
    <section className="panel"><p className="section-kicker">Общо OOF сравнение</p><h2>Представяне върху GSE25055</h2><p className="muted">Общите out-of-fold (OOF) метрики използват прогноза от fold, в който съответната пациентка не е участвала в обучението.</p>{comparison.data?.length ? <><MetricComparisonChart rows={comparison.data} /><SourceNote paths={comparison.data.map(item => item.source_path)} /></> : <EmptyState />}</section>
  </div>
}
