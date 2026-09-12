import { useQueries } from '@tanstack/react-query'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { DataQualityBanner, ErrorState, LoadingState, formatNumber, metricLabels } from '../components/Shared'
import { useExploration } from '../context/ExplorationContext'
import { datasetsMatchVerifiedContract, validationMatchesVerifiedContract } from '../dataQuality'

export function OverviewPage() {
  const { state, update, query } = useExploration()
  const [datasets, experiments, final, comparison] = useQueries({ queries: [
    { queryKey: ['datasets'], queryFn: api.datasets }, { queryKey: ['experiments'], queryFn: () => api.experiments() },
    { queryKey: ['final-validation'], queryFn: api.finalValidation }, { queryKey: ['comparison'], queryFn: api.comparison },
  ] })
  const all = [datasets, experiments, final, comparison]
  if (all.some(item => item.isLoading)) return <LoadingState />
  const failed = all.find(item => item.isError)
  if (failed) return <ErrorState error={failed.error} retry={() => all.forEach(item => item.refetch())} />
  const development = datasets.data?.find(item => item.accession === 'GSE25055')
  const external = datasets.data?.find(item => item.accession === 'GSE25065')
  const validation = final.data
  if (!development || !external || !validation) return <ErrorState error={new Error('Липсват задължителни записи за прегледа.')} retry={() => datasets.refetch()} />
  const valid = datasetsMatchVerifiedContract(datasets.data) && validationMatchesVerifiedContract(validation)
  const chart = comparison.data?.map(item => ({ name: item.model.replace('Random Forest','RF'), value: item.metrics[state.metric] }))
  const selectedModel = validation.models.find(item => item.model_key === state.model) ?? validation.models[0]

  return <div className="workspace-page overview-workspace"><header className="compact-page-header"><div><span className="section-code">RESEARCH RESULTS</span><h1>Преглед</h1><p>Кохорти, OOF сравнение, заключени конфигурации и външни резултати в един аналитичен изглед.</p></div><label className="control-field inline"><span>Метрика</span><select value={state.metric} onChange={event => update({ metric: event.target.value as typeof state.metric })}>{Object.entries(metricLabels).map(([key,label]) => <option key={key} value={key}>{label}</option>)}</select></label></header>
    <DataQualityBanner valid={valid} message={valid ? 'Ключовите стойности съвпадат с проверения договор.' : 'Ключова стойност не съвпада с проверения договор.'} />
    <div className="results-matrix"><section className="cohort-table"><h2>Кохорти</h2><table><thead><tr><th>Набор</th><th>Оригинални</th><th>Включени</th><th>RD</th><th>pCR</th><th>Probes</th></tr></thead><tbody>{[development, external].map(item => <tr key={item.accession}><th><code>{item.accession}</code></th><td>{item.original_patient_count}</td><td>{item.included_patient_count}</td><td>{item.class_distribution['0']}</td><td>{item.class_distribution['1']}</td><td>{item.feature_count.toLocaleString('bg-BG')}</td></tr>)}</tbody></table></section>
      <section className="chart-frame overview-chart"><h2>GSE25055 OOF · {metricLabels[state.metric]}</h2><ResponsiveContainer width="100%" height={205}><BarChart data={chart}><CartesianGrid stroke="#e2e5e8" vertical={false} /><XAxis dataKey="name" tick={{ fontSize: 8 }} /><YAxis domain={[0,1]} /><Tooltip /><Bar dataKey="value" fill="#5b4bdb" /></BarChart></ResponsiveContainer></section>
      <section className="locked-config"><span className="detail-index">ЗАКЛЮЧЕН</span><h2>{selectedModel.model}</h2><label className="control-field"><span>Модел</span><select value={selectedModel.model_key} onChange={event => update({ model: event.target.value })}>{validation.models.map(item => <option key={item.model_key} value={item.model_key}>{item.model}</option>)}</select></label><dl className="compact-dl">{Object.entries(selectedModel.configuration).slice(0,7).map(([key,value]) => <><dt key={`${key}k`}>{key}</dt><dd key={`${key}v`}>{String(value)}</dd></>)}</dl><Link className="text-action" to={`/process/forest?${query}`}>Отвори forest структурата <ArrowRight size={13} /></Link></section>
      <section className="external-summary"><h2>GSE25065 · заключена оценка</h2><table><thead><tr><th>Модел</th><th>Праг</th><th>ROC-AUC</th><th>PR-AUC</th><th>F1</th></tr></thead><tbody>{validation.models.map(item => <tr key={item.model_key}><th>{item.model}</th><td>{formatNumber(item.threshold,2)}</td><td>{formatNumber(item.metrics.roc_auc)}</td><td>{formatNumber(item.metrics.pr_auc)}</td><td>{formatNumber(item.metrics.f1)}</td></tr>)}</tbody></table><Link className="text-action" to={`/process/generalization?${query}`}>Сравни генерализацията <ArrowRight size={13} /></Link></section>
      <section className="matrix-pair overview-matrices">{validation.models.map(item => <div key={item.model_key}><b>{item.model}</b><table className="mini-matrix" aria-label={`Матрица на объркванията за ${item.model}`}><tbody><tr><td>{item.confusion_matrix.true_negative}</td><td>{item.confusion_matrix.false_positive}</td></tr><tr><td>{item.confusion_matrix.false_negative}</td><td>{item.confusion_matrix.true_positive}</td></tr></tbody></table></div>)}</section>
    </div>
  </div>
}
