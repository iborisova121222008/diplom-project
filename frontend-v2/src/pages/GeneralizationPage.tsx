import { useState } from 'react'
import { useQueries } from '@tanstack/react-query'
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api'
import { ChartExportActions } from '../components/ChartExport'
import { ExplorerGrid, ExplorerHeader, MetricSelect } from '../components/Explorer'
import { ErrorState, LoadingState, classLabel, formatNumber, metricLabels } from '../components/Shared'
import { useExploration } from '../context/ExplorationContext'

export function GeneralizationPage() {
  const { state, update } = useExploration()
  const [curveKind, setCurveKind] = useState<'roc' | 'precision_recall'>('roc')
  const [comparison, external, oofCurves, externalCurves, cv, disagreements] = useQueries({ queries: [
    { queryKey: ['comparison'], queryFn: api.comparison }, { queryKey: ['final-validation'], queryFn: api.finalValidation },
    { queryKey: ['curves', 'balanced-rf'], queryFn: () => api.curves('balanced-rf-nested-cv') },
    { queryKey: ['curves', 'external'], queryFn: () => api.curves('locked-external-validation-gse25065') },
    { queryKey: ['cv-results'], queryFn: () => api.cvResults() },
    { queryKey: ['disagreements', 'external'], queryFn: () => api.disagreements('locked-external-validation-gse25065', 0, 10) },
  ] })
  const all = [comparison, external, oofCurves, externalCurves, cv, disagreements]
  if (all.some(item => item.isLoading)) return <LoadingState />
  const failed = all.find(item => item.isError)
  if (failed) return <ErrorState error={failed.error} retry={() => all.forEach(item => item.refetch())} />
  const modelKey = ['custom_random_forest', 'sklearn_random_forest'].includes(state.model) ? state.model : 'custom_random_forest'
  const oof = comparison.data?.find(item => item.model_key === modelKey)
  const ext = external.data?.models.find(item => item.model_key === modelKey)
  const oofCurve = oofCurves.data?.models.find(item => item.model_key === modelKey)
  const extCurve = externalCurves.data?.models.find(item => item.model_key === modelKey)
  const oofConfusion = cv.data?.find(item => item.model_key === modelKey)?.confusion_matrix.values
  const comparisonRows = Object.keys(metricLabels).map(metric => ({ metric: metricLabels[metric], oof: oof?.metrics[metric as keyof typeof oof.metrics], external: ext?.metrics[metric as keyof typeof ext.metrics] }))
  const oofPoints = curveKind === 'roc' ? oofCurve?.roc : oofCurve?.precision_recall
  const externalPoints = curveKind === 'roc' ? extCurve?.roc : extCurve?.precision_recall
  const curveRows = [
    ...(oofPoints ?? []).map(point => ({ x: point.x, oof: point.y, external: undefined })),
    ...(externalPoints ?? []).map(point => ({ x: point.x, oof: undefined, external: point.y })),
  ].sort((left, right) => left.x - right.x)
  const selectedMetric = comparisonRows.find(item => item.metric === metricLabels[state.metric])

  return <div className="explorer-page"><ExplorerHeader title="Генерализация" description="OOF оценката върху GSE25055 срещу заключеното пренасяне към независимата GSE25065 кохорта." />
    <ExplorerGrid controls={<><label className="control-field"><span>Модел</span><select value={modelKey} onChange={event => update({ model: event.target.value })}><option value="custom_random_forest">Custom RF</option><option value="sklearn_random_forest">Sklearn RF</option></select></label><MetricSelect /><div className="tab-control"><button className={curveKind === 'roc' ? 'active' : ''} onClick={() => setCurveKind('roc')}>ROC</button><button className={curveKind === 'precision_recall' ? 'active' : ''} onClick={() => setCurveKind('precision_recall')}>PR</button></div></>}
      visualization={<><div className="comparison-strip"><span><small>GSE25055 OOF</small><b>{formatNumber(selectedMetric?.oof)}</b></span><span className="delta"><small>Разлика</small><b>{selectedMetric?.oof != null && selectedMetric.external != null ? formatNumber(selectedMetric.external - selectedMetric.oof) : '—'}</b></span><span><small>GSE25065 external</small><b>{formatNumber(selectedMetric?.external)}</b></span></div><div className="chart-frame" id="generalization-curve"><ChartExportActions targetId="generalization-curve" filename={`generalization-${modelKey}-${curveKind}`} /><h2>{curveKind === 'roc' ? 'ROC криви' : 'Precision–Recall криви'} · {ext?.model}</h2><ResponsiveContainer width="100%" height={280}><LineChart data={curveRows}><CartesianGrid stroke="#e2e5e8" /><XAxis dataKey="x" domain={[0,1]} type="number" /><YAxis domain={[0,1]} /><Tooltip /><Legend /><Line dataKey="oof" name="GSE25055 OOF" stroke="#5b4bdb" dot={false} strokeWidth={2} connectNulls /><Line dataKey="external" name="GSE25065 external" stroke="#2f6fed" dot={false} strokeWidth={2} strokeDasharray="5 3" connectNulls /></LineChart></ResponsiveContainer></div><div className="chart-frame"><h2>Разпределение на вероятностите · GSE25065</h2><ResponsiveContainer width="100%" height={180}><BarChart data={extCurve?.probability_distribution}><CartesianGrid stroke="#e2e5e8" vertical={false} /><XAxis dataKey="lower" /><YAxis /><Tooltip /><Bar dataKey="rd_count" name="RD" stackId="a" fill="#d45b50" /><Bar dataKey="pcr_count" name="pCR" stackId="a" fill="#16867a" /></BarChart></ResponsiveContainer></div></>}
      details={<><span className="detail-index">ДОКАЗАТЕЛСТВА</span><h2>{metricLabels[state.metric]}</h2><dl className="compact-dl"><dt>OOF</dt><dd>{formatNumber(selectedMetric?.oof)}</dd><dt>External</dt><dd>{formatNumber(selectedMetric?.external)}</dd><dt>Праг</dt><dd>{formatNumber(ext?.threshold, 2)}</dd><dt>Статус</dt><dd>Заключен</dd></dl><p className="evidence-note">OOF оценява задържани части от GSE25055. GSE25065 проверява пренасянето на заключения pipeline. Разликата е доказателство за генерализация, но не доказва конкретен механизъм на преобучение.</p><details className="metadata-drawer"><summary>Метаданни</summary><p>{external.data?.isolation_statement}</p></details></>}
      table={<><div className="generalization-tables"><section><h2>Метрики</h2><table><thead><tr><th>Метрика</th><th>OOF</th><th>External</th><th>Δ</th></tr></thead><tbody>{comparisonRows.map(item => <tr key={item.metric} className={item.metric === metricLabels[state.metric] ? 'selected-row' : ''}><th>{item.metric}</th><td>{formatNumber(item.oof)}</td><td>{formatNumber(item.external)}</td><td>{item.oof != null && item.external != null ? formatNumber(item.external - item.oof) : '—'}</td></tr>)}</tbody></table></section><section><h2>Матрици на объркванията</h2><div className="matrix-pair">{[['OOF', oofConfusion], ['External', ext?.confusion_matrix]].map(([label, values]) => <div key={String(label)}><b>{String(label)}</b><table className="mini-matrix"><tbody><tr><td>{(values as Record<string,number>)?.true_negative ?? (values as Record<string,number>)?.tn}</td><td>{(values as Record<string,number>)?.false_positive ?? (values as Record<string,number>)?.fp}</td></tr><tr><td>{(values as Record<string,number>)?.false_negative ?? (values as Record<string,number>)?.fn}</td><td>{(values as Record<string,number>)?.true_positive ?? (values as Record<string,number>)?.tp}</td></tr></tbody></table></div>)}</div></section><section><h2>Различия между моделите</h2><div className="table-scroll"><table><thead><tr><th>Проба</th><th>Реален</th><th>Custom</th><th>Sklearn</th></tr></thead><tbody>{disagreements.data?.items.map(item => <tr key={item.patient_id}><th><code>{item.patient_id}</code></th><td>{classLabel(item.actual_class)}</td><td>{classLabel(item.left_prediction)} · {formatNumber(item.left_probability)}</td><td>{classLabel(item.right_prediction)} · {formatNumber(item.right_probability)}</td></tr>)}</tbody></table></div></section></div></>}
    /></div>
}
