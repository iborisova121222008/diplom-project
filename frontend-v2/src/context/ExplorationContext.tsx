/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import type { MetricName } from '../types'

export interface ExplorationState {
  experiment: string
  dataset: string
  model: string
  fold: number
  metric: MetricName
  probe: string
  patient: string
  tree: number
  minimumFrequency: number
  topN: number
}

const defaults: ExplorationState = {
  experiment: 'balanced-rf-nested-cv',
  dataset: 'GSE25055',
  model: 'custom_random_forest',
  fold: 1,
  metric: 'roc_auc',
  probe: '',
  patient: '',
  tree: 1,
  minimumFrequency: 1,
  topN: 30,
}

interface ExplorationValue {
  state: ExplorationState
  update: (patch: Partial<ExplorationState>) => void
  reset: () => void
  query: string
}

const Context = createContext<ExplorationValue | null>(null)

export function ExplorationProvider({ children }: { children: React.ReactNode }) {
  const [parameters, setParameters] = useSearchParams()
  const state = useMemo<ExplorationState>(() => ({
    experiment: parameters.get('experiment') ?? defaults.experiment,
    dataset: parameters.get('dataset') ?? defaults.dataset,
    model: parameters.get('model') ?? defaults.model,
    fold: Number(parameters.get('fold') ?? defaults.fold),
    metric: (parameters.get('metric') as MetricName | null) ?? defaults.metric,
    probe: parameters.get('probe') ?? defaults.probe,
    patient: parameters.get('patient') ?? defaults.patient,
    tree: Number(parameters.get('tree') ?? defaults.tree),
    minimumFrequency: Number(parameters.get('frequency') ?? defaults.minimumFrequency),
    topN: Number(parameters.get('top') ?? defaults.topN),
  }), [parameters])

  const update = (patch: Partial<ExplorationState>) => {
    const next = new URLSearchParams(parameters)
    Object.entries(patch).forEach(([key, value]) => {
      const parameterKey = key === 'minimumFrequency' ? 'frequency' : key === 'topN' ? 'top' : key
      if (value === '' || value == null) next.delete(parameterKey)
      else next.set(parameterKey, String(value))
    })
    setParameters(next, { replace: true })
  }
  const reset = () => setParameters({}, { replace: true })

  return <Context.Provider value={{ state, update, reset, query: parameters.toString() }}>
    {children}
  </Context.Provider>
}

export function useExploration() {
  const value = useContext(Context)
  if (!value) throw new Error('ExplorationProvider is missing')
  return value
}
