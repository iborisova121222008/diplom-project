import type { Dataset, FinalValidation } from './types'

const closeTo = (actual: number | null | undefined, expected: number) =>
  actual != null && Math.abs(actual - expected) < 0.0005

export function datasetsMatchVerifiedContract(datasets: Dataset[] | undefined) {
  const development = datasets?.find(item => item.accession === 'GSE25055')
  const external = datasets?.find(item => item.accession === 'GSE25065')
  return Boolean(
    development?.included_patient_count === 306
    && development.feature_count === 22_283
    && development.class_distribution['0'] === 249
    && development.class_distribution['1'] === 57
    && external?.included_patient_count === 182
    && external.feature_count === 22_283
    && external.class_distribution['0'] === 140
    && external.class_distribution['1'] === 42
  )
}

export function validationMatchesVerifiedContract(result: FinalValidation | undefined) {
  const custom = result?.models.find(item => item.model_key === 'custom_random_forest')
  const sklearn = result?.models.find(item => item.model_key === 'sklearn_random_forest')
  return Boolean(
    result?.locked
    && closeTo(custom?.threshold, 0.21)
    && closeTo(custom?.metrics.roc_auc, 0.695)
    && closeTo(custom?.metrics.pr_auc, 0.402)
    && custom?.confusion_matrix.true_negative === 96
    && custom.confusion_matrix.false_positive === 44
    && custom.confusion_matrix.false_negative === 18
    && custom.confusion_matrix.true_positive === 24
    && closeTo(sklearn?.threshold, 0.35)
    && closeTo(sklearn?.metrics.roc_auc, 0.711)
    && closeTo(sklearn?.metrics.pr_auc, 0.407)
    && sklearn?.confusion_matrix.true_negative === 97
    && sklearn.confusion_matrix.false_positive === 43
    && sklearn.confusion_matrix.false_negative === 16
    && sklearn.confusion_matrix.true_positive === 26
  )
}
