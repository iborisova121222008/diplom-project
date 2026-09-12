import type { ReactNode } from 'react'
import { RotateCcw } from 'lucide-react'
import { useExploration } from '../context/ExplorationContext'

export function ExplorerHeader({ title, description, children }: { title: string; description: string; children?: ReactNode }) {
  const { state, reset } = useExploration()
  return <><header className="explorer-header"><div><span className="section-code">ML ПРОЦЕС</span><h1>{title}</h1><p>{description}</p></div><button className="button secondary" onClick={reset}><RotateCcw size={14} /> Нулирай</button></header>
    <div className="context-strip"><span><b>Набор</b><code>{state.dataset}</code></span><span><b>Fold</b><code>{state.fold}</code></span><span><b>Модел</b><code>{state.model}</code></span><span><b>Метрика</b><code>{state.metric}</code></span>{children}</div></>
}

export function ExplorerGrid({ controls, visualization, details, table }: { controls: ReactNode; visualization: ReactNode; details: ReactNode; table?: ReactNode }) {
  return <div className="explorer-grid"><aside className="explorer-controls">{controls}</aside><section className="explorer-main">{visualization}</section><aside className="explorer-details">{details}</aside>{table && <section className="explorer-table">{table}</section>}</div>
}

export function MetricSelect() {
  const { state, update } = useExploration()
  return <label className="control-field"><span>Метрика</span><select value={state.metric} onChange={event => update({ metric: event.target.value as typeof state.metric })}>
    <option value="roc_auc">ROC-AUC</option><option value="pr_auc">PR-AUC</option><option value="accuracy">Точност</option><option value="balanced_accuracy">Балансирана точност</option><option value="f1">F1</option><option value="precision">Прецизност</option><option value="sensitivity">Чувствителност</option><option value="specificity">Специфичност</option>
  </select></label>
}
