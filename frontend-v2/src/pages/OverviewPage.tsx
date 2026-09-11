import { useQueries } from '@tanstack/react-query'
import { ArrowRight, LockKeyhole } from 'lucide-react'
import { api } from '../api'
import { DataQualityBanner, ErrorState, LoadingState, PageHeader, SourceNote, formatNumber, metricLabels } from '../components/Shared'
import { datasetsMatchVerifiedContract, validationMatchesVerifiedContract } from '../dataQuality'

export function OverviewPage() {
  const [datasets, experiments, final] = useQueries({ queries: [
    { queryKey: ['datasets'], queryFn: api.datasets },
    { queryKey: ['experiments'], queryFn: () => api.experiments() },
    { queryKey: ['final-validation'], queryFn: api.finalValidation },
  ] })
  if (datasets.isLoading || experiments.isLoading || final.isLoading) return <LoadingState />
  const failed = [datasets, experiments, final].find(query => query.isError)
  if (failed) return <ErrorState error={failed.error} retry={() => { datasets.refetch(); experiments.refetch(); final.refetch() }} />

  const development = datasets.data?.find(item => item.accession === 'GSE25055')
  const external = datasets.data?.find(item => item.accession === 'GSE25065')
  const validation = final.data!
  const finalExperiment = experiments.data?.find(item => item.slug === 'final-model-gse25055')
  const structurallyValid = Boolean(
    development && external
    && datasetsMatchVerifiedContract(datasets.data)
    && validationMatchesVerifiedContract(validation)
    && finalExperiment?.models.every(model => model.configuration.selected_probe_count === 15)
  )

  return <div className="page">
    <PageHeader eyebrow="Проверен експеримент" title="Изследователски преглед" description="Компактен преглед на целта, кохортите, заключената конфигурация и външната проверка." />
    <DataQualityBanner valid={structurallyValid} message={structurallyValid ? 'Свързаните кохорти, финален набор и заключено състояние са налични.' : 'Свързаните записи не изпълняват проверения договор за данните.'} />
    <section className="overview-grid">
      <article className="panel emphasis"><p className="panel-label">Изследователска цел</p><h2>pCR срещу RD</h2><p>Пълен патологичен отговор спрямо остатъчна болест след химиотерапия.</p></article>
      {[development, external].map(dataset => dataset && <article className="panel" key={dataset.accession}>
        <p className="panel-label">{dataset.role === 'external_validation_only' ? 'Заключена външна кохорта' : 'Кохорта за разработване'}</p>
        <h2>{dataset.accession}</h2><div className="mini-stats"><span><strong>{dataset.included_patient_count}</strong> включени</span><span><strong>{dataset.class_distribution['0']}</strong> RD</span><span><strong>{dataset.class_distribution['1']}</strong> pCR</span></div>
      </article>)}
      <article className="panel"><p className="panel-label">Статус</p><h2><LockKeyhole size={20} /> Заключен финален модел</h2><p>{experiments.data?.length} записани експеримента; без управление на обучение.</p></article>
    </section>
    <section className="panel pipeline-panel"><h2>Път на изследването</h2><div className="pipeline">{['GSE25055', 'Подготовка', 'Nested CV', 'LASSO', 'Random Forest', 'Заключен модел', 'GSE25065'].map((item, index, all) => <span key={item}>{item}{index < all.length - 1 && <ArrowRight />}</span>)}</div></section>
    <section className="panel"><div className="section-heading"><div><p className="section-kicker">Основни резултати</p><h2>Заключена външна валидация</h2></div><span className="badge locked"><LockKeyhole size={14} /> GSE25065</span></div>
      <div className="table-scroll"><table><thead><tr><th>Модел</th><th>Праг</th>{Object.values(metricLabels).slice(0, 4).map(label => <th key={label}>{label}</th>)}</tr></thead><tbody>{validation.models.map(model => <tr key={model.model_key}><th>{model.model}</th><td>{formatNumber(model.threshold, 2)}</td>{['roc_auc','pr_auc','accuracy','balanced_accuracy'].map(metric => <td key={metric}>{formatNumber(model.metrics[metric as keyof typeof model.metrics])}</td>)}</tr>)}</tbody></table></div>
      <SourceNote paths={[validation.source_path]} />
    </section>
  </div>
}
