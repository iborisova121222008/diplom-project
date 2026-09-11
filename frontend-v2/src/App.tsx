import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { HomePage } from './pages/HomePage'
import { OverviewPage } from './pages/OverviewPage'
import { WorkflowPage } from './pages/WorkflowPage'
import { ExperimentsPage } from './pages/ExperimentsPage'
import { FeaturesPage } from './pages/FeaturesPage'
import { ExternalValidationPage } from './pages/ExternalValidationPage'
import { ReportsPage } from './pages/ReportsPage'

export default function App() {
  return <Routes>
    <Route element={<Layout />}>
      <Route index element={<HomePage />} />
      <Route path="overview" element={<OverviewPage />} />
      <Route path="workflow" element={<WorkflowPage />} />
      <Route path="experiments" element={<ExperimentsPage />} />
      <Route path="features" element={<FeaturesPage />} />
      <Route path="external-validation" element={<ExternalValidationPage />} />
      <Route path="reports" element={<ReportsPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Route>
  </Routes>
}
