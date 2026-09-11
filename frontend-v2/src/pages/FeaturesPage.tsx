import { useState } from 'react'
import { useQueries, useQuery } from '@tanstack/react-query'
import { BarChart3, Download, Info } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api'
import { StabilityChart } from '../components/Charts'
import { EmptyState, ErrorState, LoadingState, PageHeader, SourceNote, TooltipTerm, formatNumber } from '../components/Shared'

const contexts = [
  ['final-model-gse25055', 'Финален набор от 15 probe sets'],
  ['lasso-logistic-nested-cv', 'Root LASSO по fold'],
  ['balanced-rf-nested-cv', 'LASSO за balanced RF по fold'],
] as const

function FoldHeatmap({ rows }: { rows: Array<{ probe_id: string; gene_symbol: string | null; selected_folds: number[] }> }) {
  return <div className="heatmap" role="img" aria-label="Карта на избраните характеристики по fold">
    <div className="heatmap-head"><span>Probe set</span>{Array.from({ length: 10 }, (_, index) => <span key={index}>F{index + 1}</span>)}</div>
    {rows.map(row => <div className="heatmap-row" key={row.probe_id}><span title={row.probe_id}>{row.gene_symbol || row.probe_id}</span>{Array.from({ length: 10 }, (_, index) => <i key={index} className={row.selected_folds.includes(index + 1) ? 'selected' : ''} />)}</div>)}
  </div>
}

export function FeaturesPage() {
  const [experiment, setExperiment] = useState('final-model-gse25055')
  const [fold, setFold] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('probe_id')
  const [sortOrder, setSortOrder] = useState('asc')
  const [offset, setOffset] = useState(0)
  const [showCoefficients, setShowCoefficients] = useState(false)
  const limit = 25
  const features = useQuery({
    queryKey: ['features', experiment, fold, search, sortBy, sortOrder, offset],
    queryFn: () => api.features({
      experiment, fold, search, sort_by: sortBy, sort_order: sortOrder,
      offset, limit,
    }),
  })
  const [stability, heatmap, similarity, datasets, finalFeatures] = useQueries({ queries: [
    { queryKey: ['feature-stability'], queryFn: () => api.featureStability(16) },
    { queryKey: ['feature-heatmap'], queryFn: () => api.featureHeatmap(18) },
    { queryKey: ['fold-similarity'], queryFn: api.similarities },
    { queryKey: ['datasets'], queryFn: api.datasets },
    { queryKey: ['features', 'final-count'], queryFn: () => api.features({ experiment: 'final-model-gse25055', offset: 0, limit: 1 }) },
  ] })

  if (features.isLoading) return <LoadingState />
  if (features.isError) return <ErrorState error={features.error} retry={() => features.refetch()} />
  const page = features.data!
  const finalRows = experiment === 'final-model-gse25055' ? page.items : []
  const coefficientData = finalRows.map(item => ({
    name: item.annotation.gene_symbol || item.probe_id,
    coefficient: item.mean_coefficient,
  }))

  return <div className="page">
    <PageHeader eyebrow="LASSO" title="Изследване на характеристиките" description="Probe-set идентификаторите остават реалните входни характеристики; генните означения са отделна помощна анотация." actions={experiment === 'final-model-gse25055' ? <a className="button secondary" href={api.exportUrl('/api/exports/selected-probes')}><Download size={16} /> Експорт</a> : undefined} />
    <section className="panel explainer"><Info /><div><h2>Какво прави LASSO?</h2><p>LASSO свива коефициентите на по-слабо информативните характеристики до нула. Характеристиките с ненулев коефициент остават избрани за Random Forest — полезно при много повече измервания, отколкото пациентки.</p><p>Това е утвърден метод за високомерни изследователски данни, но не доказва причинна биологична връзка или клинична валидност. Корелирани probe sets могат да се избират непоследователно между fold-ове, затова се разглежда стабилността.</p></div></section>
    <section className="reduction"><span><strong>{datasets.data?.find(item => item.accession === 'GSE25055')?.feature_count.toLocaleString('bg-BG') ?? '—'}</strong> начални probe sets</span><i>→</i><span><strong>fold</strong> селекции</span><i>→</i><span><strong>{finalFeatures.data?.total ?? '—'}</strong> финални probe sets</span></section>
    <section className="panel"><form className="filters" onSubmit={event => { event.preventDefault(); setOffset(0); setSearch(searchInput) }}>
      <label>Контекст<select value={experiment} onChange={event => { setExperiment(event.target.value); setOffset(0); setFold('') }}>{contexts.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label>
      <label>Fold<select value={fold} disabled={experiment === 'final-model-gse25055'} onChange={event => { setFold(event.target.value); setOffset(0) }}><option value="">Всички</option>{Array.from({ length: 10 }, (_, index) => <option key={index} value={index + 1}>{index + 1}</option>)}</select></label>
      <label>Probe или ген<input value={searchInput} onChange={event => setSearchInput(event.target.value)} placeholder="напр. HMGXB3" /></label>
      <label>Подреждане<select value={sortBy} onChange={event => setSortBy(event.target.value)}><option value="probe_id">Probe ID</option><option value="gene_symbol">Gene symbol</option><option value="selection_frequency">Честота</option><option value="mean_coefficient">Среден коефициент</option></select></label>
      <label>Посока<select value={sortOrder} onChange={event => setSortOrder(event.target.value)}><option value="asc">Възходящо</option><option value="desc">Низходящо</option></select></label>
      <button className="button primary" type="submit">Приложи</button>
    </form>
    <p className="result-count">{page.total.toLocaleString('bg-BG')} записа</p>
    {!page.items.length ? <EmptyState text="Няма характеристики, които отговарят на филтрите." /> : <div className="table-scroll"><table><thead><tr><th><TooltipTerm term="Идентификатор на измерването върху Affymetrix микрочипа.">Probe ID</TooltipTerm></th><th>Gene symbol</th><th>Gene name</th><th>Контекст</th><th>Fold</th><th>Честота</th><th>Среден коефициент</th><th>Посока на асоциацията</th><th>Финален модел</th></tr></thead><tbody>{page.items.map(item => <tr key={`${item.experiment_slug}-${item.fold}-${item.probe_id}`}><th>{item.probe_id}</th><td>{item.annotation.gene_symbol || '—'}</td><td>{item.annotation.gene_name || '—'}</td><td>{item.selection_context}</td><td>{item.fold ?? '—'}</td><td>{item.selection_frequency == null ? '—' : formatNumber(item.selection_frequency, 2)}</td><td>{formatNumber(item.mean_coefficient, 5)}</td><td>{item.coefficient_direction === 'Higher value associated with pCR prediction' ? 'По-висока стойност е свързана с прогноза pCR' : item.coefficient_direction === 'Higher value associated with RD prediction' ? 'По-висока стойност е свързана с прогноза RD' : 'Няма записана информация'}</td><td>{item.final_model_member ? 'Да' : 'Не'}</td></tr>)}</tbody></table></div>}
    <div className="pagination"><button className="button secondary" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - limit))}>Назад</button><span>{page.total ? offset + 1 : 0}–{Math.min(offset + limit, page.total)} от {page.total}</span><button className="button secondary" disabled={offset + limit >= page.total} onClick={() => setOffset(offset + limit)}>Напред</button></div>
    <SourceNote paths={page.items.map(item => item.source_path)} /></section>

    {experiment === 'final-model-gse25055' && <section className="panel"><div className="section-heading"><div><p className="section-kicker">Статични съхранени стойности</p><h2>Коефициенти на финалния LASSO</h2></div><button className="button secondary" onClick={() => setShowCoefficients(!showCoefficients)}><BarChart3 size={16} />{showCoefficients ? 'Скрий графиката' : 'Покажи графика'}</button></div><p className="muted">Положителният коефициент е асоцииран с pCR прогноза, а отрицателният — с RD прогноза. Това не е твърдение за биологична причинност.</p>{showCoefficients && <ResponsiveContainer width="100%" height={390}><BarChart data={coefficientData} layout="vertical" margin={{ left: 35, right: 20 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} /><XAxis type="number" /><YAxis type="category" dataKey="name" width={95} tick={{ fontSize: 11 }} /><Tooltip formatter={value => Number(value).toFixed(5)} /><Bar dataKey="coefficient" name="Коефициент">{coefficientData.map((item, index) => <Cell key={index} fill={(item.coefficient ?? 0) >= 0 ? '#247d78' : '#d27768'} />)}</Bar></BarChart></ResponsiveContainer>}</section>}

    <section className="panel"><p className="section-kicker">Стабилност</p><h2>Най-често избирани LASSO характеристики</h2>{stability.isLoading ? <LoadingState /> : stability.data?.length ? <StabilityChart rows={stability.data} /> : <EmptyState />}<SourceNote paths={[stability.data?.[0]?.source_path]} /></section>
    <section className="panel"><p className="section-kicker">Fold × характеристика</p><h2>Карта на селекцията</h2><p className="muted">Оцветената клетка означава, че probe set е избран в съответния външен fold.</p>{heatmap.data?.length ? <FoldHeatmap rows={heatmap.data} /> : <EmptyState />}<SourceNote paths={[heatmap.data?.[0]?.source_path]} /></section>
    <section className="panel"><p className="section-kicker">Jaccard similarity</p><h2>Припокриване между fold селекциите</h2>{similarity.data?.length ? <div className="similarity-grid">{similarity.data.map(item => <div key={`${item.fold_a}-${item.fold_b}`} title={`${item.shared_probes} общи от ${item.union_probes}`}><small>F{item.fold_a} · F{item.fold_b}</small><strong>{formatNumber(item.jaccard_similarity, 2)}</strong></div>)}</div> : <EmptyState />}<SourceNote paths={[similarity.data?.[0]?.source_path]} /></section>
  </div>
}
