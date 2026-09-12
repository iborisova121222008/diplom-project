import type {
  Comparison, Curves, CvModel, Dataset, Disagreement, Experiment, Feature,
  FeatureHeatmap, FeatureStability, FinalValidation, FoldSimilarity, FrequencyBucket, Page,
  ForestManifest, Prediction, Report, WorkflowStep,
} from './types'

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api'

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`)
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null
    throw new Error(body?.detail ?? `Заявката към API е неуспешна (${response.status}).`)
  }
  return response.json() as Promise<T>
}

function query(path: string, values: Record<string, string | number | undefined>) {
  const parameters = new URLSearchParams()
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== '') parameters.set(key, String(value))
  })
  return `${path}?${parameters}`
}

export const api = {
  datasets: () => request<Dataset[]>('/datasets'),
  workflow: () => request<WorkflowStep[]>('/preprocessing'),
  experiments: (filters: Record<string, string> = {}) =>
    request<Experiment[]>(query('/experiments', filters)),
  features: (values: Record<string, string | number | undefined>) =>
    request<Page<Feature>>(query('/features', values)),
  featureStability: (limit = 16) =>
    request<FeatureStability[]>(`/feature-stability?limit=${limit}`),
  featureHeatmap: (limit = 18, minimumFrequency = 1, search = '') =>
    request<FeatureHeatmap[]>(query('/feature-heatmap', {
      limit, minimum_frequency: minimumFrequency, search,
    })),
  featureFrequency: () => request<FrequencyBucket[]>('/feature-frequency-distribution'),
  similarities: () => request<FoldSimilarity[]>('/fold-feature-similarity'),
  cvResults: (model?: string) =>
    request<CvModel[]>(query('/cv-results', { model })),
  comparison: () => request<Comparison[]>('/comparison'),
  finalValidation: () => request<FinalValidation>('/final-validation'),
  curves: (experiment: string) =>
    request<Curves>(query('/curves', { experiment })),
  predictions: (values: Record<string, string | number | undefined>) =>
    request<Page<Prediction>>(query('/predictions', values)),
  disagreements: (experiment: string, offset = 0, limit = 25) =>
    request<Page<Disagreement>>(query('/model-disagreements', {
      experiment, offset, limit,
    })),
  reports: () => request<Report[]>('/reports'),
  forestManifest: () => request<ForestManifest>('/forest/manifest'),
  forestTreeUrl: (tree: number) => `${API_BASE}/forest/trees/${tree}`,
  tableExportUrl: (view: string, values: Record<string, string | number | undefined>) =>
    `${API_BASE}${query(`/table-exports/${view}`, values)}`,
  exportUrl: (path: string) => `${API_BASE.replace(/\/api$/, '')}${path}`,
}
