/* eslint-disable react-refresh/only-export-components */

export function LoadingState({ label = 'Зареждане на резултатите…' }: { label?: string }) {
  return <p className="inline-state" role="status">{label}</p>
}

export function ErrorState({ retry }: { error: Error | null; retry: () => void }) {
  return <p className="inline-state error" role="alert">Данните не могат да бъдат заредени. <button onClick={retry}>Опитай отново</button></p>
}

export function EmptyState({ text = 'Няма записи за избраните филтри.' }: { text?: string }) {
  return <p className="inline-state">{text}</p>
}

export function formatNumber(value: number | null | undefined, digits = 3) {
  return value == null ? '—' : new Intl.NumberFormat('bg-BG', {
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
