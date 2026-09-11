import { useState } from 'react'
import { useQueries, useQuery } from '@tanstack/react-query'
import { Download, LockKeyhole, Trees } from 'lucide-react'
import { api } from '../api'
import { CurveChart } from '../components/Charts'
import { DataQualityBanner, EmptyState, ErrorState, LoadingState, PageHeader, SourceNote, TooltipTerm, classLabel, formatNumber, metricLabels } from '../components/Shared'
import { datasetsMatchVerifiedContract, validationMatchesVerifiedContract } from '../dataQuality'

function ConfusionMatrix({ values }: { values: Record<string, number> }) {
  return <table className="confusion-matrix" aria-label="Матрица на объркванията"><thead><tr><th /><th>Прогноза RD</th><th>Прогноза pCR</th></tr></thead><tbody><tr><th>Реално RD</th><td>{values.true_negative}</td><td>{values.false_positive}</td></tr><tr><th>Реално pCR</th><td>{values.false_negative}</td><td>{values.true_positive}</td></tr></tbody></table>
}

export function ExternalValidationPage() {
  const [model, setModel] = useState('custom_random_forest')
  const [actual, setActual] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [offset, setOffset] = useState(0)
  const limit = 25
  const [datasets, validation, curves] = useQueries({ queries: [
    { queryKey: ['datasets'], queryFn: api.datasets },
    { queryKey: ['final-validation'], queryFn: api.finalValidation },
    { queryKey: ['curves', 'external'], queryFn: () => api.curves('locked-external-validation-gse25065') },
  ] })
  const predictions = useQuery({
    queryKey: ['external-predictions', model, actual, search, offset],
    queryFn: () => api.predictions({
      experiment: 'locked-external-validation-gse25065', model,
      actual_class: actual, search, offset, limit,
    }),
  })
  const disagreements = useQuery({
    queryKey: ['external-disagreements'],
    queryFn: () => api.disagreements('locked-external-validation-gse25065', 0, 12),
  })
  if (datasets.isLoading || validation.isLoading || curves.isLoading) return <LoadingState />
  const failed = [datasets, validation, curves].find(query => query.isError)
  if (failed) return <ErrorState error={failed.error} retry={() => { datasets.refetch(); validation.refetch(); curves.refetch() }} />

  const external = datasets.data?.find(item => item.accession === 'GSE25065')
  const result = validation.data!
  const compatibility = external?.compatibility_metadata
  const qualityValid = Boolean(
    datasetsMatchVerifiedContract(datasets.data)
    && validationMatchesVerifiedContract(result)
    && compatibility?.probe_order_matches_development
    && compatibility.missing_final_probes?.length === 0
  )
  const config = result.models[0]
  const treeCount = config?.configuration.number_of_trees
    ?? config?.configuration.n_estimators

  return <div className="page">
    <PageHeader eyebrow="Независима проверка" title="Заключена външна валидация" description="GSE25065 не е използван за избор на характеристики, параметри, модел или праг." actions={<span className="badge locked large"><LockKeyhole size={16} /> Заключена</span>} />
    <DataQualityBanner valid={qualityValid} message={qualityValid ? 'Заключеният резултат и техническата съвместимост на входните probe sets са потвърдени.' : 'Липсва или не съвпада част от проверения договор за външната оценка.'} />
    <section className="overview-grid">
      <article className="panel"><p className="panel-label">Кохорта</p><h2>{external?.accession}</h2><div className="mini-stats"><span><strong>{external?.included_patient_count}</strong> пациентки</span><span><strong>{external?.class_distribution['0']}</strong> RD</span><span><strong>{external?.class_distribution['1']}</strong> pCR</span></div></article>
      <article className="panel"><p className="panel-label">Вход</p><h2>{compatibility?.required_final_probe_count} probe sets</h2><p>{compatibility?.missing_final_probes?.length === 0 ? 'Няма липсващи характеристики.' : `${compatibility?.missing_final_probes?.length} липсващи`}</p></article>
      <article className="panel"><p className="panel-label">Подредба</p><h2>{compatibility?.probe_order_matches_development ? 'Съвместима' : 'Несъвместима'}</h2><p>{compatibility?.aligned_probe_count?.toLocaleString('bg-BG')} подравнени probe IDs</p></article>
    </section>
    <section className="panel"><p className="section-kicker">Сравнение на заключените модели</p><h2>Метрики върху GSE25065</h2><div className="table-scroll"><table><thead><tr><th>Модел</th><th><TooltipTerm term="Предварително избран праг, който не се променя с външната кохорта.">Заключен праг</TooltipTerm></th>{Object.values(metricLabels).map(label => <th key={label}>{label}</th>)}</tr></thead><tbody>{result.models.map(item => <tr key={item.model_key}><th>{item.model}</th><td>{formatNumber(item.threshold, 2)}</td>{Object.keys(metricLabels).map(key => <td key={key}>{formatNumber(item.metrics[key as keyof typeof item.metrics])}</td>)}</tr>)}</tbody></table></div><SourceNote paths={[result.source_path]} /></section>
    <div className="two-charts"><CurveChart models={curves.data!.models} kind="roc" /><CurveChart models={curves.data!.models} kind="precision_recall" /></div>
    <section className="matrix-grid">{result.models.map(item => <article className="panel" key={item.model_key}><h2>{item.model}</h2><p className="muted">Праг: {formatNumber(item.threshold, 2)}</p><ConfusionMatrix values={item.confusion_matrix} /></article>)}</section>
    <section className="panel explainer"><Trees /><div><h2>Как работи Random Forest?</h2><p>Random Forest е ансамбъл от decision trees. Дърветата разглеждат bootstrap извадки и случайни поднабори от характеристики, а финалната вероятност обединява прогнозите им.</p><p>Това е утвърден метод за таблични данни, но може да се преобучи при малки и шумни набори. Тук резултатът се проверява чрез кръстосана и заключена външна валидация; не се твърди клинична валидност.</p><div className="principle"><span>{compatibility?.required_final_probe_count ?? '—'} избрани probe sets</span><b>→</b><span>{String(treeCount ?? '—')} дървета</span><b>→</b><span>обединена вероятност</span><b>→</b><span>заключен праг</span><b>→</b><span>RD / pCR</span></div><small>Обяснение на принципа — не е повторение на обучението.</small></div></section>
    <section className="panel"><p className="section-kicker">Техническа съвместимост</p><h2>Сравнение на мащаба на експресията</h2><p className="muted">Тези перцентили са техническа проверка, а не оценка за биологично сходство или domain-shift score.</p>{compatibility?.scale_percentiles?.length ? <div className="table-scroll"><table><thead><tr>{Object.keys(compatibility.scale_percentiles[0]).map(key => <th key={key}>{key}</th>)}</tr></thead><tbody>{compatibility.scale_percentiles.map((row, index) => <tr key={index}>{Object.values(row).map((value, cell) => <td key={cell}>{formatNumber(value, cell === 0 ? 0 : 3)}</td>)}</tr>)}</tbody></table></div> : <EmptyState />}<SourceNote paths={compatibility?.source_paths ?? []} /></section>
    <section className="panel"><div className="section-heading"><div><p className="section-kicker">Съхранени индивидуални резултати</p><h2>Таблица с външни прогнози</h2></div><a className="button secondary" href={api.exportUrl('/api/exports/external-predictions')}><Download size={16} /> Експорт</a></div><form className="filters" onSubmit={event => { event.preventDefault(); setOffset(0); setSearch(searchInput) }}><label>Модел<select value={model} onChange={event => { setModel(event.target.value); setOffset(0) }}>{result.models.map(item => <option value={item.model_key} key={item.model_key}>{item.model}</option>)}</select></label><label>Реален клас<select value={actual} onChange={event => { setActual(event.target.value); setOffset(0) }}><option value="">Всички</option><option value="0">RD</option><option value="1">pCR</option></select></label><label>Patient ID<input value={searchInput} onChange={event => setSearchInput(event.target.value)} /></label><button className="button primary">Приложи</button></form>
      {predictions.isLoading ? <LoadingState /> : predictions.data?.items.length ? <><div className="table-scroll"><table><thead><tr><th>Patient ID</th><th>Реален клас</th><th>Прогноза</th><th>pCR вероятност</th><th>Модел</th></tr></thead><tbody>{predictions.data.items.map(item => <tr key={`${item.model_key}-${item.patient_id}`}><th>{item.patient_id}</th><td>{classLabel(item.actual_class)}</td><td>{classLabel(item.predicted_class)}</td><td>{formatNumber(item.probability)}</td><td>{item.model}</td></tr>)}</tbody></table></div><div className="pagination"><button className="button secondary" disabled={!offset} onClick={() => setOffset(Math.max(0, offset - limit))}>Назад</button><span>{offset + 1}–{Math.min(offset + limit, predictions.data.total)} от {predictions.data.total}</span><button className="button secondary" disabled={offset + limit >= predictions.data.total} onClick={() => setOffset(offset + limit)}>Напред</button></div></> : <EmptyState />}
    </section>
    <section className="panel"><p className="section-kicker">Съпоставка</p><h2>Случаи с различна прогноза от двата модела</h2>{disagreements.data?.items.length ? <div className="table-scroll"><table><thead><tr><th>Patient ID</th><th>Реален клас</th><th>Custom RF</th><th>Вероятност</th><th>Sklearn RF</th><th>Вероятност</th></tr></thead><tbody>{disagreements.data.items.map(item => <tr key={item.patient_id}><th>{item.patient_id}</th><td>{classLabel(item.actual_class)}</td><td>{classLabel(item.left_prediction)}</td><td>{formatNumber(item.left_probability)}</td><td>{classLabel(item.right_prediction)}</td><td>{formatNumber(item.right_probability)}</td></tr>)}</tbody></table></div> : <EmptyState text="Няма записани различия между прогнозите." />}</section>
  </div>
}
