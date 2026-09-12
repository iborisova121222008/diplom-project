export type MetricName =
  | 'roc_auc' | 'pr_auc' | 'accuracy' | 'balanced_accuracy'
  | 'f1' | 'precision' | 'sensitivity' | 'specificity'

export type Metrics = Partial<Record<MetricName, number | null>>

export interface Dataset {
  accession: string
  role: string
  included_patient_count: number
  original_patient_count: number
  excluded_patient_count: number
  feature_count: number
  label_mapping: Record<string, number>
  class_distribution: Record<string, number>
  source_path: string
  provenance: Record<string, unknown>
  compatibility_metadata: {
    technical_check_only?: boolean
    aligned_probe_count?: number
    probe_order_matches_development?: boolean
    required_final_probe_count?: number
    missing_final_probes?: string[]
    scale_percentiles?: Array<Record<string, number>>
    source_paths?: string[]
  }
}

export interface WorkflowStep {
  order: number
  category: string
  title: string
  detail: string
  source_path: string
  source_cell: string
}

export interface ModelRun {
  model_key: string
  display_name: string
  model_family: string
  configuration: Record<string, unknown>
  configuration_source_path: string | null
  overall_metrics: Metrics
  fold_count: number
}

export interface Experiment {
  slug: string
  name: string
  dataset: string
  evaluation_stage: string
  result_scope: string
  locked: boolean
  status: 'completed' | 'locked'
  source_path: string
  created_at: string | null
  models: ModelRun[]
}

export interface Feature {
  experiment_slug: string
  experiment_name: string
  selection_context: string
  fold: number | null
  probe_id: string
  coefficient: number | null
  mean_coefficient: number | null
  selected_folds: number | null
  selection_frequency: number | null
  coefficient_direction: string | null
  final_model_member: boolean
  source_path: string
  source_fields: Record<string, unknown>
  annotation: {
    gene_symbol: string | null
    gene_name: string | null
    entrez_id: string | null
    number_of_genes: number | null
    mapping_status: string
    display_only: boolean
    source_path: string
  }
}

export interface Page<T> { total: number; offset: number; limit: number; items: T[] }

export interface FoldResult {
  fold: number
  training_patient_count: number | null
  validation_patient_count: number | null
  selected_probe_count: number | null
  selected_parameters: Record<string, unknown>
  metrics: Metrics
  result_type: string
  source_path: string
}

export interface CvModel {
  model_key: string
  model: string
  experiment_slug: string
  experiment_name: string
  dataset: string
  folds: FoldResult[]
  summary: {
    metrics: Record<MetricName, { mean: number | null; std: number | null }>
    result_type: string
    source_type: string
    source_path: string
    derivation: string | null
  }
  confusion_matrix: {
    values: Record<string, number>
    source_path: string
  }
}

export interface Comparison {
  model_key: string
  model: string
  experiment_slug: string
  dataset: string
  result_type: string
  metrics: Metrics
  source_path: string
}

export interface FinalValidation {
  experiment: string
  experiment_slug: string
  dataset: string
  dataset_role: string
  locked: boolean
  result_type: string
  evaluated_at: string | null
  source_path: string
  isolation_statement: string
  models: Array<{
    model_key: string
    model: string
    threshold: number
    configuration: Record<string, unknown>
    metrics: Metrics
    confusion_matrix: Record<string, number>
    source_path: string
  }>
}

export interface Prediction {
  experiment_slug: string
  model_key: string
  model: string
  patient_id: string
  actual_class: number
  predicted_class: number
  probability: number
  validation_fold: number | null
  source_path: string
}

export interface ModelCurve {
  model_key: string
  model: string
  roc: Array<{ x: number; y: number; threshold: number | null }>
  precision_recall: Array<{ x: number; y: number; threshold: number | null }>
  probability_distribution: Array<{
    lower: number; upper: number; rd_count: number; pcr_count: number
  }>
  source_path: string
}

export interface Curves {
  experiment_slug: string
  result_type: string
  models: ModelCurve[]
}

export interface Disagreement {
  patient_id: string
  actual_class: number
  left_model_key: string
  left_prediction: number
  left_probability: number
  right_model_key: string
  right_prediction: number
  right_probability: number
}

export interface FeatureStability {
  probe_id: string
  gene_symbol: string | null
  selected_folds: number
  selection_frequency: number
  mean_coefficient: number | null
  coefficient_direction: string | null
  final_model_member: boolean
  source_path: string
}

export interface FeatureHeatmap {
  probe_id: string
  gene_symbol: string | null
  selection_frequency: number
  selected_folds: number[]
  source_path: string
}

export interface FrequencyBucket {
  selected_folds: number
  probe_count: number
}

export interface FoldSimilarity {
  experiment_slug: string
  fold_a: number
  fold_b: number
  shared_probes: number
  union_probes: number
  jaccard_similarity: number
  source_path: string
}

export interface Report {
  key: string
  title: string
  description: string
  format: string
  download_url: string
  source_paths: string[]
}

export interface TreeFeatureUsage {
  probe_id: string
  split_count: number
  minimum_split_depth: number | null
  mean_split_depth: number | null
}

export interface TreeSummary {
  tree_index: number
  full_depth: number
  node_count: number
  generated_depth: number
  used_probes: string[]
  feature_usage: TreeFeatureUsage[]
  asset: string
}

export interface ForestFeatureUsage {
  probe_id: string
  trees_using: number
  split_count: number
  minimum_split_depth: number | null
  mean_split_depth: number | null
  tree_indices: number[]
}

export interface ForestManifest {
  derivation: string
  generated_at_utc: string
  model_package: string
  model_package_identity: string
  model_created_at_utc: string | null
  tree_count: number
  custom_tree_count: number
  selected_probes: string[]
  generated_depth: number
  trees: TreeSummary[]
  feature_usage: ForestFeatureUsage[]
}
