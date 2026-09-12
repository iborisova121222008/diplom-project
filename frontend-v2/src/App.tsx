import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { LoadingState } from './components/Shared'
import { ExplorationProvider } from './context/ExplorationContext'

const HomePage = lazy(() => import('./pages/HomePage').then(module => ({ default: module.HomePage })))
const OverviewPage = lazy(() => import('./pages/OverviewPage').then(module => ({ default: module.OverviewPage })))
const ExperimentsPage = lazy(() => import('./pages/ExperimentsPage').then(module => ({ default: module.ExperimentsPage })))
const ExternalValidationPage = lazy(() => import('./pages/ExternalValidationPage').then(module => ({ default: module.ExternalValidationPage })))
const ReportsPage = lazy(() => import('./pages/ReportsPage').then(module => ({ default: module.ReportsPage })))
const ProcessOverviewPage = lazy(() => import('./pages/ProcessOverviewPage').then(module => ({ default: module.ProcessOverviewPage })))
const NestedCvPage = lazy(() => import('./pages/NestedCvPage').then(module => ({ default: module.NestedCvPage })))
const LassoExplorerPage = lazy(() => import('./pages/LassoExplorerPage').then(module => ({ default: module.LassoExplorerPage })))
const ForestExplorerPage = lazy(() => import('./pages/ForestExplorerPage').then(module => ({ default: module.ForestExplorerPage })))
const GeneralizationPage = lazy(() => import('./pages/GeneralizationPage').then(module => ({ default: module.GeneralizationPage })))

export default function App() {
  return <ExplorationProvider><Suspense fallback={<LoadingState label="Зареждане на работното пространство…" />}><Routes>
    <Route element={<Layout />}>
      <Route index element={<HomePage />} />
      <Route path="overview" element={<OverviewPage />} />
      <Route path="experiments" element={<ExperimentsPage />} />
      <Route path="external-validation" element={<ExternalValidationPage />} />
      <Route path="reports" element={<ReportsPage />} />
      <Route path="process" element={<ProcessOverviewPage />} />
      <Route path="process/nested-cv" element={<NestedCvPage />} />
      <Route path="process/lasso" element={<LassoExplorerPage />} />
      <Route path="process/forest" element={<ForestExplorerPage />} />
      <Route path="process/generalization" element={<GeneralizationPage />} />
      <Route path="workflow" element={<Navigate to="/process" replace />} />
      <Route path="features" element={<Navigate to="/process/lasso" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Route>
  </Routes></Suspense></ExplorationProvider>
}
