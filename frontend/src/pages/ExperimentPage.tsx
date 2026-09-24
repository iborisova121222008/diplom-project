import { useState } from 'react'
import { useQueries, useQuery } from '@tanstack/react-query'
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { NavLink, Navigate, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api'
import { ChartExportActions } from '../components/ChartExport'
import { EmptyState, ErrorState, LoadingState, classLabel, formatNumber, metricLabels } from '../components/Shared'
import type { MetricName, Metrics, Prediction } from '../types'

const tabs = [
  ['input', 'Входни данни'],
  ['preparation', 'Подготовка на данните'],
  ['features', 'Избрани характеристики'],
  ['evaluation', 'Оценка на моделите'],
  ['predictions', 'Прогнози'],
] as const

type TabKey = (typeof tabs)[number][0]
const metricKeys: MetricName[] = ['roc_auc', 'pr_auc', 'accuracy', 'balanced_accuracy', 'f1', 'precision', 'sensitivity', 'specificity']
const parameterLabels: Record<string, string> = { best_C: 'Избрано C', best_class_weight: 'Баланс на класовете', class_weight: 'Баланс на класовете' }
const displayValue = (value: unknown) => value === 'balanced' ? 'балансирано тегло' : String(value)

function Header({ title, purpose }: { title: string; purpose: string }) {
  return <header className="tab-heading"><h1>{title}</h1><p>{purpose}</p></header>
}

function Exports({ csv, xlsx }: { csv: string; xlsx: string }) {
  return <span className="exports"><button type="button" onClick={() => void api.download(csv)}>CSV</button><button type="button" onClick={() => void api.download(xlsx)}>XLSX</button></span>
}

function InputTab() {
  const [dataset, setDataset] = useState('GSE25055')
  const [patient, setPatient] = useState('')
  const [probe, setProbe] = useState('')
  const [rowOffset, setRowOffset] = useState(0)
  const [columnOffset, setColumnOffset] = useState(0)
  const values = { dataset, patient_search: patient, probe_search: probe, row_offset: rowOffset, row_limit: 8, column_offset: columnOffset, column_limit: 8 }
  const [datasets, preview] = useQueries({ queries: [
    { queryKey: ['datasets'], queryFn: api.datasets },
    { queryKey: ['expression-preview', values], queryFn: () => api.expressionPreview(values) },
  ] })
  if (datasets.isLoading || preview.isLoading) return <LoadingState />
  const failed = datasets.isError ? datasets : preview.isError ? preview : null
  if (failed) return <ErrorState error={failed.error} retry={() => { datasets.refetch(); preview.refetch() }} />
  const data = preview.data!
  const csv = api.expressionExportUrl({ ...values, format: 'csv' })
  const xlsx = api.expressionExportUrl({ ...values, format: 'xlsx' })
  return <><Header title="Входни данни" purpose="Кохортите и малък прозорец от подравнената входна матрица на генна експресия." />
    <table className="cohort-table"><thead><tr><th>Кохорта</th><th>Роля</th><th>Първоначално</th><th>Включени</th><th>Изключени</th><th>Съвместими probe sets</th></tr></thead><tbody>{datasets.data?.map(item => <tr key={item.accession}><th>{item.accession}</th><td>{item.accession === 'GSE25055' ? 'Разработване' : 'Независима оценка; проверени наличие и ред'}</td><td>{item.original_patient_count}</td><td>{item.included_patient_count}</td><td>{item.excluded_patient_count}</td><td>{item.feature_count.toLocaleString('bg-BG')}</td></tr>)}</tbody></table>
    <div className="toolbar"><label>Набор<select value={dataset} onChange={event => { setDataset(event.target.value); setRowOffset(0); setColumnOffset(0) }}><option>GSE25055</option><option>GSE25065</option></select></label><label>Пациент<input value={patient} onChange={event => { setPatient(event.target.value); setRowOffset(0) }} placeholder="GSM…" /></label><label>Probe set<input value={probe} onChange={event => { setProbe(event.target.value); setColumnOffset(0) }} placeholder="204…" /></label><Exports csv={csv} xlsx={xlsx} /></div>
    <p className="single-note">Една ML характеристика е експресионната стойност на един Affymetrix probe set.</p>
    <section className="data-panel"><div className="panel-title"><h2>Входна матрица на генна експресия</h2><span>{data.total_patients} пациентки × {data.total_probes.toLocaleString('bg-BG')} probe sets след филтриране</span></div>{data.patients.length && data.probes.length ? <div className="table-scroll matrix-scroll"><table className="matrix-table"><thead><tr><th>Пациент</th>{data.probes.map(item => <th key={item}>{item}</th>)}</tr></thead><tbody>{data.patients.map((id, row) => <tr key={id}><th>{id}</th>{data.values[row].map((value, column) => <td key={data.probes[column]}>{formatNumber(value, 2)}</td>)}</tr>)}</tbody></table></div> : <EmptyState />}
      <div className="pager"><button disabled={rowOffset === 0} onClick={() => setRowOffset(Math.max(0, rowOffset - 8))}>Предишни пациенти</button><span>{rowOffset + 1}–{Math.min(rowOffset + 8, data.total_patients)}</span><button disabled={rowOffset + 8 >= data.total_patients} onClick={() => setRowOffset(rowOffset + 8)}>Следващи пациенти</button><button disabled={columnOffset === 0} onClick={() => setColumnOffset(Math.max(0, columnOffset - 8))}>Предишни probe sets</button><span>{columnOffset + 1}–{Math.min(columnOffset + 8, data.total_probes)}</span><button disabled={columnOffset + 8 >= data.total_probes} onClick={() => setColumnOffset(columnOffset + 8)}>Следващи probe sets</button></div>
    </section></>
}

function PreparationTab() {
  const [fold, setFold] = useState(1)
  const [workflow, cv] = useQueries({ queries: [
    { queryKey: ['workflow'], queryFn: api.workflow },
    { queryKey: ['cv-results', 'lasso_logistic'], queryFn: () => api.cvResults('lasso_logistic') },
  ] })
  if (workflow.isLoading || cv.isLoading) return <LoadingState />
  const failed = workflow.isError ? workflow : cv.isError ? cv : null
  if (failed) return <ErrorState error={failed.error} retry={() => { workflow.refetch(); cv.refetch() }} />
  const selected = cv.data?.[0]?.folds.find(item => item.fold === fold)
  const rows = [
    ['Експресия и клиничен отговор', 'Подравняване на идентификаторите', '306 валидни пациентки'],
    ['Клиничен отговор', 'Кодиране на класовете', 'RD = 0 / pCR = 1'],
    ['GSE25055', '10 външни разделяния', 'Всяка пациентка се оценява веднъж'],
    ['Външна обучаваща част', 'Стандартизация и 5-fold inner CV', 'Параметри и fold-local селекция'],
    ['Fold-local probe sets', 'Обучение на собствен и sklearn RF само върху обучаващата част', 'Два fold-local модела'],
    ['Задържана външна част', 'Еднократно прогнозиране', 'OOF доказателство за оценката'],
  ]
  return <><Header title="Подготовка на данните" purpose="Подравняването и nested CV предпазват оценката от използване на информация от задържаните пациентки." />
    <div className="process-line" aria-label="Последователност на подготовката">{['Експресия + клиничен отговор', 'Подравняване на идентификатори', 'RD = 0 / pCR = 1', 'Проверки', '10 външни fold-а', 'Стандартизация и 5-fold inner CV само в обучаващата част'].map((item, index) => <span key={item}>{item}{index < 5 && <b>→</b>}</span>)}</div>
    <div className="toolbar"><label>Външен fold<select value={fold} onChange={event => setFold(Number(event.target.value))}>{Array.from({ length: 10 }, (_, index) => <option key={index + 1} value={index + 1}>Fold {index + 1}</option>)}</select></label><Exports csv={api.tableExportUrl('fold-results', { experiment: 'lasso-logistic-nested-cv', fold, format: 'csv' })} xlsx={api.tableExportUrl('fold-results', { experiment: 'lasso-logistic-nested-cv', fold, format: 'xlsx' })} /></div>
    <p className="single-note">Няма една глобално стандартизирана матрица: стандартизацията се напасва отделно във всяка обучаваща част.</p>
    <section className="split-layout"><table><thead><tr><th>Вход</th><th>Операция</th><th>Резултат</th></tr></thead><tbody>{rows.map(row => <tr key={row[0]}>{row.map((cell, index) => index ? <td key={cell}>{cell}</td> : <th key={cell}>{cell}</th>)}</tr>)}</tbody></table><table><thead><tr><th colSpan={2}>Fold {fold}</th></tr></thead><tbody><tr><th>Обучаващи пациентки</th><td>{selected?.training_patient_count ?? '—'}</td></tr><tr><th>Валидиращи пациентки</th><td>{selected?.validation_patient_count ?? '—'}</td></tr><tr><th>Избрани probe sets</th><td>{selected?.selected_probe_count ?? '—'}</td></tr>{Object.entries(selected?.selected_parameters ?? {}).map(([key, value]) => <tr key={key}><th>{parameterLabels[key] ?? 'Параметър'}</th><td>{displayValue(value)}</td></tr>)}</tbody></table></section>
    <details className="settings"><summary>Проверени стъпки</summary><table><tbody>{workflow.data?.map(item => <tr key={item.order}><th>{item.title}</th><td>{item.detail}</td></tr>)}</tbody></table></details></>
}

type FeatureView = 'heatmap' | 'coefficients'
function FeaturesTab() {
  const [view, setView] = useState<FeatureView>('heatmap')
  const [fold, setFold] = useState('')
  const [minimum, setMinimum] = useState(1)
  const [search, setSearch] = useState('')
  const [finalOnly, setFinalOnly] = useState(false)
  const [selectedProbe, setSelectedProbe] = useState('')
  const [stability, heatmap, finalFeatures] = useQueries({ queries: [
    { queryKey: ['feature-stability', minimum, search, finalOnly], queryFn: () => api.featureStability({ limit: 30, minimum_frequency: minimum, search, final_only: finalOnly ? 1 : 0 }) },
    { queryKey: ['feature-heatmap', minimum, search], queryFn: () => api.featureHeatmap(30, minimum, search) },
    { queryKey: ['final-features'], queryFn: () => api.features({ experiment: 'final-model-gse25055', limit: 100, sort_by: 'probe_id' }) },
  ] })
  const all = [stability, heatmap, finalFeatures]
  if (all.some(item => item.isLoading)) return <LoadingState />
  const failed = all.find(item => item.isError)
  if (failed) return <ErrorState error={failed.error} retry={() => all.forEach(item => item.refetch())} />
  const finals = finalFeatures.data?.items ?? []
  const heatmapRows = (heatmap.data ?? []).filter(item =>
    (!fold || item.selected_folds.includes(Number(fold)))
    && (!finalOnly || finals.some(final => final.probe_id === item.probe_id))
  )
  const rows = (fold ? heatmapRows : stability.data ?? []).map(item => ({
    probe_id: item.probe_id,
    gene_symbol: item.gene_symbol,
    selected_folds: Array.isArray(item.selected_folds) ? item.selected_folds.length : item.selected_folds,
    selection_frequency: item.selection_frequency,
  }))
  const chosen = selectedProbe || (view === 'coefficients' ? finals[0]?.probe_id : rows[0]?.probe_id)
  const exportView = view === 'coefficients' ? 'features' : 'feature-stability'
  const exportValues = view === 'coefficients'
    ? { experiment: 'final-model-gse25055', search, format: 'csv' }
    : { fold: fold || undefined, search, minimum_frequency: minimum, final_only: finalOnly ? 1 : 0, format: 'csv' }
  return <><Header title="Избрани характеристики" purpose="Fold-local LASSO селекциите показват стабилност, а отделният финален fit определя 15-те входа на заключения модел." />
    <div className="branch-flow"><span>Fold-local LASSO селекции → <b>2 015</b> избрани поне веднъж → <b>72</b> в анализа на стабилността</span><span>Отделен финален LASSO fit върху целия GSE25055 → <b>15</b> финални probe sets</span></div>
    <div className="view-tabs" role="tablist">{[['heatmap','Fold × характеристика'],['coefficients','Финални коефициенти']].map(([key,label]) => <button role="tab" aria-selected={view === key} key={key} onClick={() => setView(key as FeatureView)}>{label}</button>)}</div>
    <div className="toolbar"><label>Външен fold<select value={fold} onChange={event => setFold(event.target.value)}><option value="">Всички fold-ове</option>{Array.from({ length: 10 }, (_, index) => <option key={index + 1} value={index + 1}>Fold {index + 1}</option>)}</select></label><label>Минимална честота<select value={minimum} onChange={event => setMinimum(Number(event.target.value))}>{Array.from({ length: 10 }, (_, index) => <option key={index + 1} value={index + 1}>{index + 1}/10</option>)}</select></label><label>Probe set или ген<input value={search} onChange={event => setSearch(event.target.value)} /></label><label className="check"><input type="checkbox" checked={finalOnly} onChange={event => setFinalOnly(event.target.checked)} /> Само финалните 15</label><Exports csv={api.tableExportUrl(exportView, exportValues)} xlsx={api.tableExportUrl(exportView, { ...exportValues, format: 'xlsx' })} /></div>
    <section className="linked-view">
      <div className="chart-panel" id="feature-chart"><ChartExportActions targetId="feature-chart" filename={`lasso-${view}`} />
        {view === 'heatmap' && <div className="heatmap"><div className="heat-row head"><span>Probe set</span>{Array.from({length:10},(_,i)=><b key={i}>F{i+1}</b>)}</div>{heatmapRows.map(item => <button key={item.probe_id} className={`heat-row ${chosen === item.probe_id ? 'selected' : ''}`} onClick={() => setSelectedProbe(item.probe_id)}><span>{item.probe_id}</span>{Array.from({length:10},(_,i)=><i key={i} className={item.selected_folds.includes(i+1) ? 'on' : ''}>{item.selected_folds.includes(i+1) ? '●' : '·'}</i>)}</button>)}</div>}
        {view === 'coefficients' && <ResponsiveContainer width="100%" height={340}><BarChart data={finals} layout="vertical" margin={{ left: 25 }}><CartesianGrid stroke="#d9e0e6" horizontal={false} /><XAxis type="number" /><YAxis type="category" dataKey="probe_id" width={105} tick={{ fontSize: 10 }} /><Tooltip /><Bar dataKey="coefficient" name="Коефициент" onClick={(_, index) => setSelectedProbe(finals[index].probe_id)}>{finals.map(item => <Cell key={item.probe_id} fill={(item.coefficient ?? 0) >= 0 ? '#167b83' : '#a85359'} />)}</Bar></BarChart></ResponsiveContainer>}
      </div>
      <div className="table-scroll linked-table"><table><thead><tr><th>Probe set</th><th>Ген</th><th>Fold-ове</th><th>Честота</th><th>Финален коефициент</th><th>Финален модел</th></tr></thead><tbody>{(view === 'coefficients' ? finals.map(item => ({ probe_id: item.probe_id, gene_symbol: item.annotation.gene_symbol, selected_folds: null, selection_frequency: null })) : rows).map(item => { const final = finals.find(value => value.probe_id === item.probe_id); return <tr key={item.probe_id} className={chosen === item.probe_id ? 'selected-row' : ''} onClick={() => setSelectedProbe(item.probe_id)}><th>{item.probe_id}</th><td>{item.gene_symbol ?? '—'}</td><td>{item.selected_folds ?? '—'}</td><td>{formatNumber(item.selection_frequency, 1)}</td><td>{formatNumber(final?.coefficient, 5)}</td><td>{final ? 'Да' : 'Не'}</td></tr>})}</tbody></table></div>
    </section>
    {view === 'coefficients' && <p className="single-note">Отрицателните стойности са свързани с прогноза RD, а положителните — с прогноза pCR; това не е причинно биологично твърдение.</p>}
    <details className="settings"><summary>Настройки</summary><table><tbody><tr><th>Вътрешни разделяния</th><td>5</td></tr><tr><th>Баланс на класовете</th><td>balanced</td></tr><tr><th>Финално C</th><td>0.03</td></tr></tbody></table></details></>
}

type ModelChoice = 'custom_random_forest' | 'sklearn_random_forest' | 'comparison'
function EvaluationTab() {
  const [cohort, setCohort] = useState<'oof' | 'external'>('oof')
  const [model, setModel] = useState<ModelChoice>('comparison')
  const [view, setView] = useState<'roc' | 'precision_recall'>('roc')
  const [comparison, external, oofCurves, externalCurves, cv] = useQueries({ queries: [
    { queryKey: ['comparison'], queryFn: api.comparison },
    { queryKey: ['final-validation'], queryFn: api.finalValidation },
    { queryKey: ['curves', 'oof'], queryFn: () => api.curves('balanced-rf-nested-cv') },
    { queryKey: ['curves', 'external'], queryFn: () => api.curves('locked-external-validation-gse25065') },
    { queryKey: ['cv-results'], queryFn: () => api.cvResults() },
  ] })
  const all = [comparison, external, oofCurves, externalCurves, cv]
  if (all.some(item => item.isLoading)) return <LoadingState />
  const failed = all.find(item => item.isError)
  if (failed) return <ErrorState error={failed.error} retry={() => all.forEach(item => item.refetch())} />
  const keys = model === 'comparison' ? ['custom_random_forest','sklearn_random_forest'] : [model]
  const metricsRows = keys.map(key => cohort === 'oof' ? comparison.data?.find(item => item.model_key === key) : external.data?.models.find(item => item.model_key === key)).filter(Boolean) as Array<{model_key:string;model:string;metrics:Metrics;confusion_matrix?:Record<string,number>}>
  const curves = (cohort === 'oof' ? oofCurves.data : externalCurves.data)?.models.filter(item => keys.includes(item.model_key)) ?? []
  const matrixFor = (key: string) => cohort === 'external' ? external.data?.models.find(item => item.model_key === key)?.confusion_matrix : cv.data?.find(item => item.model_key === key)?.confusion_matrix.values
  const colors = ['#167b83','#425e8a']
  return <><Header title="Оценка на моделите" purpose="Вътрешните OOF резултати от GSE25055 и еднократната независима оценка върху GSE25065." />
    <div className="toolbar"><label>Кохорта<select value={cohort} onChange={event => setCohort(event.target.value as 'oof'|'external')}><option value="oof">GSE25055 OOF</option><option value="external">GSE25065 външна</option></select></label><label>Модел<select value={model} onChange={event => setModel(event.target.value as ModelChoice)}><option value="custom_random_forest">Собствен RF</option><option value="sklearn_random_forest">sklearn RF</option><option value="comparison">Сравнение</option></select></label><label>Крива<select value={view} onChange={event => setView(event.target.value as 'roc'|'precision_recall')}><option value="roc">ROC</option><option value="precision_recall">PR</option></select></label><ChartExportActions targetId="evaluation-chart" filename={`${cohort}-${view}`} /><Exports csv={api.tableExportUrl('metrics', { cohort, model, format: 'csv' })} xlsx={api.tableExportUrl('metrics', { cohort, model, format: 'xlsx' })} /></div>
    <section className="evaluation-layout"><div className="chart-panel" id="evaluation-chart"><ResponsiveContainer width="100%" height={330}><LineChart margin={{left:0,right:18}}><CartesianGrid stroke="#d9e0e6" /><XAxis type="number" dataKey="x" domain={[0,1]} /><YAxis type="number" dataKey="y" domain={[0,1]} /><Tooltip /><Legend />{curves.map((item,index)=><Line key={item.model_key} data={item[view]} dataKey="y" name={item.model_key === 'custom_random_forest' ? 'Собствен RF' : 'sklearn RF'} stroke={colors[index]} dot={false} strokeWidth={2} isAnimationActive={false} />)}</LineChart></ResponsiveContainer></div><div className="matrix-area">{metricsRows.map(item => { const matrix=matrixFor(item.model_key) ?? {}; return <table className="confusion" key={item.model_key}><caption>{model === 'comparison' ? (item.model_key === 'custom_random_forest' ? 'Собствен RF' : 'sklearn RF') : 'Матрица на объркванията'}</caption><thead><tr><th></th><th>Прогноза RD</th><th>Прогноза pCR</th></tr></thead><tbody><tr><th>Реално RD</th><td>{matrix.true_negative ?? matrix.tn}</td><td>{matrix.false_positive ?? matrix.fp}</td></tr><tr><th>Реално pCR</th><td>{matrix.false_negative ?? matrix.fn}</td><td>{matrix.true_positive ?? matrix.tp}</td></tr></tbody></table> })}</div></section>
    <div className="table-scroll"><table><thead><tr><th>Модел</th>{metricKeys.map(key => <th key={key}>{metricLabels[key]}</th>)}</tr></thead><tbody>{metricsRows.map(item => <tr key={item.model_key}><th>{item.model_key === 'custom_random_forest' ? 'Собствен RF' : 'sklearn RF'}</th>{metricKeys.map(key => <td key={key}>{formatNumber(item.metrics[key])}</td>)}</tr>)}</tbody></table></div>
    <table className="difference-table"><thead><tr><th>Сравнение</th><th>Наблюдение</th></tr></thead><tbody><tr><th>Източник на вътрешната оценка</th><td>306 OOF прогнози от десетте задържани части на GSE25055</td></tr><tr><th>Източник на външната оценка</th><td>182 независими пациентки от GSE25065 след заключване на конфигурацията</td></tr></tbody></table></>
}

function PredictionsTab() {
  const [dataset, setDataset] = useState<'GSE25055'|'GSE25065'>('GSE25055')
  const [model, setModel] = useState('custom_random_forest')
  const [actual, setActual] = useState('')
  const [predicted, setPredicted] = useState('')
  const [correct, setCorrect] = useState('')
  const [disagreement, setDisagreement] = useState('')
  const [search, setSearch] = useState('')
  const [minimum, setMinimum] = useState('')
  const [maximum, setMaximum] = useState('')
  const [offset, setOffset] = useState(0)
  const [sortBy, setSortBy] = useState('patient_id')
  const [sortOrder, setSortOrder] = useState<'asc'|'desc'>('asc')
  const experiment = dataset === 'GSE25055' ? 'balanced-rf-nested-cv' : 'locked-external-validation-gse25065'
  const filters = { experiment, model, actual_class: actual, predicted_class: predicted, correct, disagreement, search, minimum_probability: minimum, maximum_probability: maximum, sort_by: sortBy, sort_order: sortOrder, offset, limit: 25 }
  const predictions = useQuery({ queryKey: ['predictions', filters], queryFn: () => api.predictions(filters) })
  if (predictions.isLoading) return <LoadingState />
  if (predictions.isError) return <ErrorState error={predictions.error} retry={() => predictions.refetch()} />
  const page = predictions.data!
  const setPreset = (value: 'all'|'wrong'|'different') => { setCorrect(value === 'wrong' ? 'false' : ''); setDisagreement(value === 'different' ? 'true' : ''); setOffset(0) }
  const sort = (column: string) => { if (sortBy === column) setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc'); else { setSortBy(column); setSortOrder('asc') } }
  const resetPage = (setter: (value: string) => void) => (value: string) => { setter(value); setOffset(0) }
  return <><Header title="Прогнози" purpose="Записаната прогноза на всеки заключен модел за всяка включена пациентка." />
    <div className="facts"><span><b>{page.total}</b> видими записа</span><span><b>{page.correct ?? '—'}</b> правилни</span><span><b>{page.incorrect ?? '—'}</b> неправилни</span><span><b>{page.disagreements ?? '—'}</b> разлики между моделите</span></div>
    <div className="presets"><button onClick={() => setPreset('all')}>Всички</button><button onClick={() => setPreset('wrong')}>Неправилни</button><button onClick={() => setPreset('different')}>Разлики между моделите</button></div>
    <div className="toolbar wrap"><label>Набор<select value={dataset} onChange={event => { setDataset(event.target.value as 'GSE25055'|'GSE25065'); setOffset(0) }}><option>GSE25055</option><option>GSE25065</option></select></label><label>Модел<select value={model} onChange={event => resetPage(setModel)(event.target.value)}><option value="custom_random_forest">Собствен RF</option><option value="sklearn_random_forest">sklearn RF</option></select></label><label>Реален клас<select value={actual} onChange={event => resetPage(setActual)(event.target.value)}><option value="">Всички</option><option value="0">RD</option><option value="1">pCR</option></select></label><label>Прогнозиран клас<select value={predicted} onChange={event => resetPage(setPredicted)(event.target.value)}><option value="">Всички</option><option value="0">RD</option><option value="1">pCR</option></select></label><label>Резултат<select value={correct} onChange={event => resetPage(setCorrect)(event.target.value)}><option value="">Всички</option><option value="true">Правилни</option><option value="false">Неправилни</option></select></label><label>Моделите<select value={disagreement} onChange={event => resetPage(setDisagreement)(event.target.value)}><option value="">Всички</option><option value="true">Различни</option><option value="false">Еднакви</option></select></label><label>Пациент<input value={search} onChange={event => resetPage(setSearch)(event.target.value)} /></label><label>Вероятност от<input type="number" min="0" max="1" step="0.05" value={minimum} onChange={event => resetPage(setMinimum)(event.target.value)} /></label><label>до<input type="number" min="0" max="1" step="0.05" value={maximum} onChange={event => resetPage(setMaximum)(event.target.value)} /></label><Exports csv={api.tableExportUrl('predictions', { ...filters, format: 'csv', offset: undefined, limit: undefined })} xlsx={api.tableExportUrl('predictions', { ...filters, format: 'xlsx', offset: undefined, limit: undefined })} /></div>
    <div className="table-scroll predictions-table"><table><thead><tr>{[['patient_id','Пациент'],['dataset','Набор'],['actual_class','Реален клас'],['probability','pCR вероятност'],['predicted_class','Прогнозиран клас'],['result','Резултат'],['model','Модел']].map(([key,label]) => <th key={key}>{['patient_id','actual_class','probability','predicted_class'].includes(key) ? <button onClick={() => sort(key)}>{label}{sortBy === key ? (sortOrder === 'asc' ? ' ↑' : ' ↓') : ''}</button> : label}</th>)}</tr></thead><tbody>{page.items.map((item: Prediction) => <tr key={`${item.model_key}-${item.patient_id}`}><th>{item.patient_id}</th><td>{dataset}</td><td><span className={`class-mark ${classLabel(item.actual_class).toLowerCase()}`}>{classLabel(item.actual_class)}</span></td><td>{formatNumber(item.probability, 4)}</td><td><span className={`class-mark ${classLabel(item.predicted_class).toLowerCase()}`}>{classLabel(item.predicted_class)}</span></td><td>{item.actual_class === item.predicted_class ? 'Правилна' : 'Неправилна'}</td><td>{item.model_key === 'custom_random_forest' ? 'Собствен RF' : 'sklearn RF'}</td></tr>)}</tbody></table></div>
    <div className="pager"><button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 25))}>Предишни</button><span>{page.total ? offset + 1 : 0}–{Math.min(offset + 25, page.total)} от {page.total}</span><button disabled={offset + 25 >= page.total} onClick={() => setOffset(offset + 25)}>Следващи</button></div></>
}

export function ExperimentPage() {
  const { tab } = useParams()
  const [, setSearch] = useSearchParams()
  const active = (tabs.some(([key]) => key === tab) ? tab : tab == null ? 'input' : null) as TabKey | null
  if (!active) return <Navigate to="/experiment/input" replace />
  const content = { input: <InputTab />, preparation: <PreparationTab />, features: <FeaturesTab />, evaluation: <EvaluationTab />, predictions: <PredictionsTab /> }[active]
  return <div className="experiment-page">
    <nav className="subtabs" aria-label="Етапи на експеримента">{tabs.map(([key,label]) => <NavLink key={key} to={`/experiment/${key}`} onClick={() => setSearch({})}>{label}</NavLink>)}</nav>
    <div className="tab-content">{content}</div>
  </div>
}
