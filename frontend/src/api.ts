import type {
  Comparison, Curves, CvModel, Dataset, Disagreement, Experiment, Feature,
  FeatureHeatmap, FeatureStability, FinalValidation, FoldSimilarity, FrequencyBucket, Page,
  ExpressionPreview, ForestManifest, ForestStructure, Prediction, Report, WorkflowStep,
} from './types'
import { clearStoredAuth, readStoredAuth } from './authStorage'

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

function authHeaders(json = false): HeadersInit {
  const session = readStoredAuth()
  return {
    ...(json ? { 'Content-Type': 'application/json' } : {}),
    ...(session ? { Authorization: `Bearer ${session.accessToken}` } : {}),
  }
}

async function checkedResponse(url: string, options: RequestInit = {}) {
  let response: Response
  try {
    response = await fetch(url, options)
  } catch {
    throw new Error('Връзката със сървъра е неуспешна.')
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null
    if (response.status === 401 && !url.includes('/auth/')) {
      clearStoredAuth()
      window.dispatchEvent(new Event('research-auth-expired'))
    }
    throw new Error(body?.detail ?? `Заявката към API е неуспешна (${response.status}).`)
  }
  return response
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await checkedResponse(`${API_BASE}${path}`, {
    ...options,
    headers: { ...authHeaders(options.body !== undefined), ...options.headers },
  })
  return response.json() as Promise<T>
}

async function download(url: string) {
  const response = await checkedResponse(url, { headers: authHeaders() })
  const blob = await response.blob()
  const disposition = response.headers.get('content-disposition') ?? ''
  const filename = disposition.match(/filename="?([^";]+)"?/i)?.[1] ?? 'export'
  const objectUrl = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(objectUrl)
}

function query(path: string, values: Record<string, string | number | undefined>) {
  const parameters = new URLSearchParams()
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== '') parameters.set(key, String(value))
  })
  return `${path}?${parameters}`
}

export const api = {
  register: (researcher_id: string, password: string) =>
    request<{ access_token: string; token_type: 'bearer'; researcher_id: string }>('/auth/register', {
      method: 'POST', body: JSON.stringify({ researcher_id, password }),
    }),
  login: (researcher_id: string, password: string) =>
    request<{ access_token: string; token_type: 'bearer'; researcher_id: string }>('/auth/login', {
      method: 'POST', body: JSON.stringify({ researcher_id, password }),
    }),
  download,
  datasets: () => request<Dataset[]>('/datasets'),
  expressionPreview: (values: Record<string, string | number | undefined>) =>
    request<ExpressionPreview>(query('/expression-preview', values)),
  expressionExportUrl: (values: Record<string, string | number | undefined>) =>
    `${API_BASE}${query('/expression-preview/export', values)}`,
  workflow: () => request<WorkflowStep[]>('/preprocessing'),
  experiments: (filters: Record<string, string> = {}) =>
    request<Experiment[]>(query('/experiments', filters)),
  features: (values: Record<string, string | number | undefined>) =>
    request<Page<Feature>>(query('/features', values)),
  featureStability: (values: Record<string, string | number | undefined> = {}) =>
    request<FeatureStability[]>(query('/feature-stability', values)),
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
  forestStructure: (implementation: string, tree: number, depth: number) =>
    request<ForestStructure>(query('/forest/structure', {
      implementation, tree_index: tree, visible_depth: depth,
    })),
  forestTreeUrl: (tree: number) => `${API_BASE}/forest/trees/${tree}`,
  tableExportUrl: (view: string, values: Record<string, string | number | undefined>) =>
    `${API_BASE}${query(`/table-exports/${view}`, values)}`,
  exportUrl: (path: string) => `${API_BASE.replace(/\/api$/, '')}${path}`,
}
