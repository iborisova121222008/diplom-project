import { useQuery } from '@tanstack/react-query'
import { CheckCircle2, ShieldCheck } from 'lucide-react'
import { api } from '../api'
import { EmptyState, ErrorState, LoadingState, PageHeader, SourceNote } from '../components/Shared'

const leakageChecks = [
  'StandardScaler е fitted само върху обучаващата част на fold-а.',
  'LASSO е fitted само върху обучаващата част на fold-а.',
  'Валидационният fold не участва в избора на характеристики.',
  'Праговете са избрани само от GSE25055 OOF прогнози.',
  'GSE25065 е изключен от настройването и избора.',
  'Моделите и праговете са заключени преди външната оценка.',
]

export function WorkflowPage() {
  const query = useQuery({ queryKey: ['workflow'], queryFn: api.workflow })
  if (query.isLoading) return <LoadingState />
  if (query.isError) return <ErrorState error={query.error} retry={() => query.refetch()} />
  if (!query.data?.length) return <EmptyState />
  return <div className="page">
    <PageHeader eyebrow="Възпроизводимост" title="Работен процес" description="Реалната последователност от подготовката на GEO данните до еднократната заключена оценка." />
    <section className="workflow-list">{query.data.map(step => <details className="workflow-step" key={step.order}>
      <summary><span>{step.order}</span><div><small>{step.category}</small><strong>{step.title}</strong></div></summary>
      <div className="step-details"><p>{step.detail}</p><dl><dt>Операция и резултат</dt><dd>{step.detail}</dd><dt>Източник</dt><dd>{step.source_path} · {step.source_cell}</dd></dl></div>
    </details>)}</section>
    <section className="panel protection"><div className="section-heading"><div><p className="section-kicker">Методологичен контрол</p><h2>Защита срещу изтичане на информация</h2></div><ShieldCheck size={28} /></div>
      <div className="check-grid">{leakageChecks.map(check => <p key={check}><CheckCircle2 size={18} />{check}</p>)}</div>
      <SourceNote paths={query.data.map(step => step.source_path)} />
    </section>
    <section className="panel"><h2>Какво е преобучение?</h2><p>Преобучение възниква, когато моделът запомня особености и шум от обучаващите данни, но не се представя добре върху нови пациентки.</p><p className="muted">Налични са fold и OOF резултати плюс заключена външна оценка. Обучаващи метрики не са записани, затова не се показва измислена разлика „train–validation“ или оценка на риска.</p></section>
  </div>
}
