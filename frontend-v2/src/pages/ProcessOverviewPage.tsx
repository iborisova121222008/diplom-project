import { useQueries } from '@tanstack/react-query'
import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { EmptyState, ErrorState, LoadingState } from '../components/Shared'
import { useExploration } from '../context/ExplorationContext'

export function ProcessOverviewPage() {
  const { query } = useExploration()
  const [datasets, cv, final] = useQueries({ queries: [
    { queryKey: ['datasets'], queryFn: api.datasets },
    { queryKey: ['cv-results'], queryFn: () => api.cvResults() },
    { queryKey: ['final-validation'], queryFn: api.finalValidation },
  ] })
  if ([datasets, cv, final].some(item => item.isLoading)) return <LoadingState />
  const failed = [datasets, cv, final].find(item => item.isError)
  if (failed) return <ErrorState error={failed.error} retry={() => { datasets.refetch(); cv.refetch(); final.refetch() }} />
  const development = datasets.data?.find(item => item.accession === 'GSE25055')
  const external = datasets.data?.find(item => item.accession === 'GSE25065')
  if (!development || !external) return <EmptyState />
  const finalProbeCount = final.data?.models[0]?.configuration.selected_probe_count as number
  const customThreshold = final.data?.models.find(item => item.model_key === 'custom_random_forest')?.threshold
  const sklearnThreshold = final.data?.models.find(item => item.model_key === 'sklearn_random_forest')?.threshold
  const checkpoints = [
    ['01', 'Подготовка и подравняване', `${development.original_patient_count} → ${development.included_patient_count} GSE25055 пациентки · ${development.feature_count.toLocaleString('bg-BG')} probes`, '/overview'],
    ['02', 'Външни fold-ове', `${cv.data?.[0]?.folds.length} външни дяла върху GSE25055`, '/process/nested-cv'],
    ['03', 'Вътрешен LASSO избор', '5-fold CV само във всяка outer training част; параметри и fold-local probes', '/process/nested-cv'],
    ['04', 'Fold-local Random Forest', 'Custom и sklearn се обучават само върху outer training частта и нейните probes', '/process/nested-cv'],
    ['05', 'Held-out прогноза', 'Прогноза за външния валидационен fold, изключен от селекцията', '/process/nested-cv'],
    ['06', 'OOF обединяване', `${development.included_patient_count} прогнози от десетте held-out части`, '/process/generalization'],
    ['07', 'Сравнение и прагове', 'Само GSE25055 OOF evidence се използва за сравнение и избор на праг', '/process/generalization'],
    ['08', 'Заключване', `Custom ${customThreshold} · sklearn ${sklearnThreshold}`, '/process/generalization'],
    ['09', 'Финален LASSO fit', `Пълен GSE25055 · C=0.03 · ${finalProbeCount} подредени probes`, '/process/lasso'],
    ['10', 'Финални forests', `Два модела × ${final.data?.models[0]?.configuration.number_of_trees ?? final.data?.models[1]?.configuration.n_estimators} дървета върху пълния GSE25055`, '/process/forest'],
    ['11', 'Заключен пакет', 'Записване и проверено презареждане на fitted package', '/process/forest'],
    ['12', 'GSE25065 съвместимост', `${external.original_patient_count} → ${external.included_patient_count}; probe наличие и ред`, '/external-validation'],
    ['13', 'Еднократно прилагане', `${external.included_patient_count} пациентки · заключени модели и прагове`, '/external-validation'],
  ]
  return <div className="workspace-page process-page">
    <header className="compact-page-header"><span className="section-code">ML ПРОЦЕС</span><h1>Карта на експеримента</h1><p>Избираем преглед на реалните записани контролни точки — не възпроизвеждане на обучение в реално време.</p></header>
    <div className="journey-grid">{checkpoints.map(([number, title, evidence, path]) => <Link key={number} to={`${path}?${query}`} className="journey-step"><span>{number}</span><h2>{title}</h2><p>{evidence}</p><b>Отвори <ArrowRight size={14} /></b></Link>)}</div>
    <section className="method-note"><strong>Граница на доказателствата</strong><p>Вътрешни fold метрики, coefficient path, training curves и OOB история не са записани и не се реконструират.</p></section>
  </div>
}
