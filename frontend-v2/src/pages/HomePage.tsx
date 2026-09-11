import { useQuery } from '@tanstack/react-query'
import { ArrowRight, BookOpen, Dna, Microscope, ScanSearch } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { bulgariaCancerFacts } from '../content/bulgariaCancerFacts'
import { ErrorState, LoadingState, TooltipTerm } from '../components/Shared'

const story = (featureCount?: number, externalCount?: number) => [
  {
    icon: Dna,
    title: 'Биологични различия',
    text: 'Една и съща диагноза не означава напълно еднаква биология на тумора. Разликите в активността на гените могат да бъдат свързани с начина, по който туморът реагира на лечението.',
  },
  {
    icon: Microscope,
    title: 'Генна експресия',
    text: `За всяка пациентка са измерени ${featureCount?.toLocaleString('bg-BG') ?? '—'} сигнала за генна експресия. Всеки сигнал представя приблизителната активност на определен генен участък, измерена чрез Affymetrix probe set.\n\nРазглеждани поотделно, тези измервания трудно описват цялостното поведение на тумора. Заедно те образуват молекулярен профил, в който машинното обучение може да търси комбинации и закономерности, свързани с отговора към химиотерапията.`,
  },
  {
    icon: ScanSearch,
    title: 'Различен отговор към химиотерапията',
    text: 'След химиотерапията при част от пациентките не се установява остатъчна инвазивна болест — пълен патологичен отговор, pCR. При други остава резидуална болест, RD.\n\nЦелта на експеримента е да се провери дали профилът на генна експресия преди лечението съдържа достатъчно информация за прогнозиране на тази разлика.',
  },
  {
    icon: BookOpen,
    title: 'AI-assisted predictor',
    text: `Machine learning превръща хиляди молекулярни измервания в проверима прогноза. LASSO избира малък набор от информативни характеристики, а Random Forest търси комбинации между тях.\n\nЗаключеният модел се оценява върху независима група от ${externalCount ?? '—'} пациентки, които не са участвали в обучението, избора на характеристики, параметрите или прага за класификация.`,
  },
]

export function HomePage() {
  const datasets = useQuery({ queryKey: ['datasets'], queryFn: api.datasets })
  if (datasets.isLoading) return <LoadingState />
  if (datasets.isError) return <ErrorState error={datasets.error} retry={() => datasets.refetch()} />

  const development = datasets.data?.find(item => item.accession === 'GSE25055')
  const external = datasets.data?.find(item => item.accession === 'GSE25065')

  return <div className="landing-page">
    <section className="hero">
      <div className="hero-copy">
        <p className="eyebrow">Мотивацията зад експеримента</p>
        <h1>Една диагноза.<br />Различна биология.<br /><em>Различен отговор.</em></h1>
        <p className="hero-text">Пациентки с една и съща диагноза могат да имат различни молекулярни профили и да реагират различно на една и съща химиотерапия. Прецизната онкология изследва дали тези биологични различия могат да помогнат да се предвиди при кои пациентки лечението има най-голяма вероятност да постигне пълен патологичен отговор.</p>
        <div className="hero-actions">
          <a href="#scientific-story" className="button primary">Проследи научната идея <ArrowRight size={17} /></a>
          <Link to="/overview" className="button secondary">Отвори изследователския преглед</Link>
        </div>
      </div>
    </section>

    <section id="scientific-story" className="landing-section">
      <p className="section-kicker">Научна идея</p>
      <h2>Какво се опитва да предвиди изследването?</h2>
      <div className="story-timeline">
        {story(development?.feature_count, external?.included_patient_count).map(({ icon: Icon, title, text }, index) => <article key={title}>
          <div className="timeline-number">{index + 1}</div>
          <Icon size={22} /><h3>{title}</h3><p>{text}</p>
          {index === 1 && <TooltipTerm term="Probe set е група от сонди върху микрочипа, използвана за измерване на генната експресия. Probe-set ID е характеристиката за модела, а gene symbol и gene name служат за биологична интерпретация.">Какво е probe set?</TooltipTerm>}
        </article>)}
      </div>
    </section>

    <section className="scale-section">
      <div><strong>{development?.feature_count.toLocaleString('bg-BG')}</strong><span>сигнала за генна експресия за всяка пациентка</span></div>
      <div><strong>{development?.included_patient_count}</strong><span>пациентки за разработване и кръстосана валидация, GSE25055</span></div>
      <div><strong>{external?.included_patient_count}</strong><span>пациентки за заключена външна валидация, GSE25065; не са използвани при разработването</span></div>
    </section>

    <section className="landing-section context-section">
      <div><p className="section-kicker">Контекст за България</p><h2>Ракът на гърдата остава важен общественоздравен въпрос</h2></div>
      <div className="facts-grid">{bulgariaCancerFacts.map(fact => <article key={fact.label}>
        <strong>{fact.value}</strong><p>{fact.label}</p><small>{fact.year}</small>
      </article>)}</div>
      <a className="source-link" href={bulgariaCancerFacts[0].sourceUrl} target="_blank" rel="noreferrer">{bulgariaCancerFacts[0].sourceName} <ArrowRight size={14} /></a>
    </section>
  </div>
}
