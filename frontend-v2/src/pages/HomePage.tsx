import { useQuery } from '@tanstack/react-query'
import { ArrowRight, BarChart3, Network } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { ErrorState, LoadingState } from '../components/Shared'
import { bulgariaCancerFacts } from '../content/bulgariaCancerFacts'

export function HomePage() {
  const datasets = useQuery({ queryKey: ['datasets'], queryFn: api.datasets })
  if (datasets.isLoading) return <LoadingState />
  if (datasets.isError) return <ErrorState error={datasets.error} retry={() => datasets.refetch()} />
  const development = datasets.data?.find(item => item.accession === 'GSE25055')
  const external = datasets.data?.find(item => item.accession === 'GSE25065')
  return <div className="workspace-page home-workspace">
    <header className="home-title"><span className="section-code">РАК НА ГЪРДАТА · ЗАВЪРШЕН ML ЕКСПЕРИМЕНТ</span><h1>Молекулярен отговор</h1><p>Работно пространство за проверка на записаните LASSO и Random Forest резултати и за проследяване на реалния експериментален процес.</p></header>
    <div className="home-choices">
      <Link to="/overview" className="home-choice"><BarChart3 /><span>01 / РЕЗУЛТАТИ</span><h2>Изследователски резултати</h2><p>Сравнете експерименти, модели, метрики, прогнози и заключената външна валидация.</p><b>Отвори прегледа <ArrowRight /></b></Link>
      <Link to="/process" className="home-choice accent"><Network /><span>02 / ML ПРОЦЕС</span><h2>ML Process Explorer</h2><p>Проследете nested CV, fold-local LASSO, стабилността, fitted forest структурата и генерализацията.</p><b>Отвори процеса <ArrowRight /></b></Link>
    </div>
    <div className="home-data-strip"><span><b>{development?.original_patient_count} → {development?.included_patient_count}</b>GSE25055</span><span><b>{development?.feature_count.toLocaleString('bg-BG')}</b>подравнени probe sets</span><span><b>{external?.original_patient_count} → {external?.included_patient_count}</b>GSE25065</span><span><b>RD / pCR</b>изследователска цел</span></div>
    <details className="references"><summary>Референции за контекста в България</summary><ol>{bulgariaCancerFacts.map(fact => <li key={fact.label}><b>{fact.value}</b> — {fact.label} ({fact.year}). <a href={fact.sourceUrl} target="_blank" rel="noreferrer">{fact.sourceName}</a></li>)}</ol></details>
  </div>
}
