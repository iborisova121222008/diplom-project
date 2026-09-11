/* eslint-disable react-refresh/only-export-components */
import type { ReactNode } from 'react'
import { AlertTriangle, DatabaseZap, RefreshCw } from 'lucide-react'

export const unavailableText = 'Тази визуализация не е налична, защото необходимите резултати не са записани за този експеримент.'

export function PageHeader({ eyebrow, title, description, actions }: {
  eyebrow?: string; title: string; description: string; actions?: ReactNode
}) {
  return <header className="content-header">
    <div>{eyebrow && <p className="eyebrow">{eyebrow}</p>}<h1>{title}</h1><p>{description}</p></div>
    {actions && <div className="header-actions">{actions}</div>}
  </header>
}

export function LoadingState({ label = 'Зареждане на проверените резултати…' }: { label?: string }) {
  return <div className="state-panel" role="status"><span className="loader" />{label}</div>
}

export function ErrorState({ error, retry }: { error: Error | null; retry: () => void }) {
  return <div className="state-panel error" role="alert">
    <DatabaseZap /><div><strong>Данните не могат да бъдат заредени.</strong><p>{error?.message}</p></div>
    <button className="button secondary" onClick={retry}><RefreshCw size={16} />Опитай отново</button>
  </div>
}

export function EmptyState({ text = unavailableText }: { text?: string }) {
  return <div className="state-panel empty"><AlertTriangle /><p>{text}</p></div>
}

export function SourceNote({ paths }: { paths: Array<string | null | undefined> }) {
  const visible = [...new Set(paths.filter(Boolean))] as string[]
  if (!visible.length) return null
  return <p className="source-note"><strong>Източник на данните:</strong> {visible.join(' · ')}</p>
}

export function TooltipTerm({ term, children }: { term: string; children: ReactNode }) {
  return <span className="tooltip-term" tabIndex={0} data-tooltip={term}>{children}</span>
}

export function formatNumber(value: number | null | undefined, digits = 3) {
  return value == null ? 'Няма данни' : new Intl.NumberFormat('bg-BG', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value)
}

export function classLabel(value: number) { return value === 1 ? 'pCR' : 'RD' }

export const metricLabels: Record<string, string> = {
  roc_auc: 'ROC-AUC', pr_auc: 'PR-AUC', accuracy: 'Точност',
  balanced_accuracy: 'Балансирана точност', f1: 'F1', precision: 'Прецизност',
  sensitivity: 'Чувствителност', specificity: 'Специфичност',
}

export function DataQualityBanner({ valid, message }: { valid: boolean; message: string }) {
  return <div className={valid ? 'quality-banner valid' : 'quality-banner invalid'}>
    {valid ? '✓' : '!'} <span>{message}</span>
  </div>
}
